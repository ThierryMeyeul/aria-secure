from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
import pyotp
import qrcode
import base64
from io import BytesIO

from .models import User, LoginAttempt
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    MFAVerifySerializer, MFASetupSerializer, MFAEnableSerializer,
    MFADisableSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    RefreshTokenSerializer, LogoutSerializer, UserProfileUpdateSerializer
)


def get_client_ip(request):
    """Récupère l'adresse IP du client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login_attempt(email, request, result, failure_reason='', user=None):
    """Enregistre une tentative de connexion."""
    LoginAttempt.objects.create(
        email=email,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        result=result,
        failure_reason=failure_reason,
        user=user
    )


def get_tokens_for_user(user):
    """Génère les tokens JWT pour un utilisateur."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouvel utilisateur."""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Compte créé avec succès.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Première étape de connexion - Vérification email/password."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Log de la tentative réussie (première étape)
        log_login_attempt(
            email=user.email,
            request=request,
            result='success',
            user=user
        )
        
        # Mettre à jour last_login_ip
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login_ip'])
        
        # Générer un token temporaire pour la vérification MFA
        temp_token = RefreshToken.for_user(user)
        temp_token['temp'] = True
        temp_token.set_exp(lifetime=timezone.timedelta(minutes=5))
        
        response_data = {
            'message': 'Identifiants corrects.',
            'mfa_required': user.has_mfa_enabled(),
            'temp_token': str(temp_token),
            'user_id': str(user.id),
        }
        
        if not user.has_mfa_enabled():
            # Pas de MFA, on retourne directement les tokens
            tokens = get_tokens_for_user(user)
            response_data['tokens'] = tokens
            response_data['user'] = UserSerializer(user).data
        
        return Response(response_data, status=status.HTTP_200_OK)


class MFAVerifyView(APIView):
    """Vérification du code MFA (deuxième étape de connexion)."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        temp_token = serializer.validated_data['temp_token']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            # Décoder le token temporaire
            token = RefreshToken(temp_token)
            user_id = token.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Vérifier le code TOTP
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(otp_code, valid_window=1):
                log_login_attempt(
                    email=user.email,
                    request=request,
                    result='failed',
                    failure_reason='Code MFA invalide',
                    user=user
                )
                return Response(
                    {'error': 'Code MFA invalide.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # MFA valide
            log_login_attempt(
                email=user.email,
                request=request,
                result='success',
                user=user
            )
            
            # Générer les tokens définitifs
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'Authentification réussie.',
                'tokens': tokens,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response(
                {'error': 'Token temporaire invalide ou expiré.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class MFASetupView(APIView):
    """Configuration initiale de MFA - Génère le secret et le QR code."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MFASetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Vérifier le mot de passe
        if not user.check_password(serializer.validated_data['password']):
            return Response(
                {'error': 'Mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Générer un nouveau secret TOTP
        secret = pyotp.random_base32()
        
        # Stocker temporairement dans la session
        request.session['mfa_temp_secret'] = secret
        
        # Générer l'URI pour le QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=getattr(settings, 'MFA_ISSUER_NAME', 'ARIA Secure')
        )
        
        # Générer le QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'provisioning_uri': provisioning_uri
        }, status=status.HTTP_200_OK)


class MFAEnableView(APIView):
    """Active MFA après vérification du code."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MFAEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        otp_code = serializer.validated_data['otp_code']
        temp_secret = request.session.get('mfa_temp_secret')
        
        if not temp_secret:
            return Response(
                {'error': 'Aucune configuration MFA en cours.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier le code
        totp = pyotp.TOTP(temp_secret)
        if not totp.verify(otp_code, valid_window=1):
            return Response(
                {'error': 'Code invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Activer MFA
        user.mfa_secret = temp_secret
        user.mfa_enabled = True
        user.save()
        
        # Nettoyer la session
        del request.session['mfa_temp_secret']
        
        return Response({
            'message': 'MFA activé avec succès.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class MFADisableView(APIView):
    """Désactive MFA."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MFADisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        password = serializer.validated_data['password']
        otp_code = serializer.validated_data['otp_code']
        
        # Vérifier le mot de passe
        if not user.check_password(password):
            return Response(
                {'error': 'Mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Vérifier le code MFA
        if user.has_mfa_enabled():
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(otp_code, valid_window=1):
                return Response(
                    {'error': 'Code MFA invalide.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Désactiver MFA
        user.mfa_secret = ''
        user.mfa_enabled = False
        user.save()
        
        return Response({
            'message': 'MFA désactivé avec succès.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    """Change le mot de passe de l'utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Ancien mot de passe incorrect.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Mot de passe changé avec succès.'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Demande de réinitialisation de mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email'].lower()
        
        try:
            user = User.objects.get(email=email)
            
            # Générer un token de réinitialisation
            reset_token = RefreshToken.for_user(user)
            reset_token['purpose'] = 'password_reset'
            reset_token.set_exp(lifetime=timezone.timedelta(hours=1))
            
            # Envoyer l'email (simulation console en dev)
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            
            # TODO: Envoyer vrai email en production
            print(f"Password reset link for {email}: {reset_link}")
            
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe
            pass
        
        return Response({
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Confirmation de réinitialisation de mot de passe."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            token = RefreshToken(token_str)
            
            if token.get('purpose') != 'password_reset':
                return Response(
                    {'error': 'Token invalide.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user_id = token.get('user_id')
            user = User.objects.get(id=user_id)
            
            user.set_password(new_password)
            user.save()
            
            # Blacklister le token
            token.blacklist()
            
            return Response({
                'message': 'Mot de passe réinitialisé avec succès.'
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response(
                {'error': 'Token invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshTokenView(APIView):
    """Rafraîchit le token JWT."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response(
                {'error': 'Token de rafraîchissement invalide ou expiré.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """Déconnexion - Blacklist le refresh token."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            refresh.blacklist()
            
            log_login_attempt(
                email=request.user.email,
                request=request,
                result='logout',
                user=request.user
            )
            
            return Response({
                'message': 'Déconnexion réussie.'
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response(
                {'error': 'Token invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Récupère et met à jour le profil utilisateur."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer
    
    def get_object(self):
        return self.request.user


class UserDetailView(generics.RetrieveAPIView):
    """Récupère les détails d'un utilisateur (admin seulement)."""
    
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'


class UserListView(generics.ListAPIView):
    """Liste tous les utilisateurs (admin seulement)."""
    
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset