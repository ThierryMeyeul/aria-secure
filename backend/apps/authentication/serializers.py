from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, RefreshToken, LoginAttempt
import pyotp
import qrcode
import base64
from io import BytesIO


class UserSerializer(serializers.ModelSerializer):
    """Serializer de base pour le modèle User."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'mfa_enabled', 'email_verified', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email_verified', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value.lower()
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        email = validated_data.pop('email')
        
        user = User.objects.create_user(
            email=email,
            password=password,
            **{k: v for k, v in validated_data.items()}
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer pour la première étape de connexion."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Email ou mot de passe incorrect."})
        
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Email ou mot de passe incorrect."})
        
        if not user.is_active:
            raise serializers.ValidationError({"email": "Ce compte est désactivé."})
        
        attrs['user'] = user
        return attrs


class MFAVerifySerializer(serializers.Serializer):
    """Serializer pour la vérification du code MFA."""
    
    temp_token = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Le code doit contenir uniquement des chiffres.")
        return value


class MFASetupSerializer(serializers.Serializer):
    """Serializer pour la configuration MFA."""
    
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})


class MFAEnableSerializer(serializers.Serializer):
    """Serializer pour activer MFA après configuration."""
    
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Le code doit contenir uniquement des chiffres.")
        return value


class MFADisableSerializer(serializers.Serializer):
    """Serializer pour désactiver MFA."""
    
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe."""
    
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Les mots de passe ne correspondent pas."})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer pour demander la réinitialisation du mot de passe."""
    
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer pour confirmer la réinitialisation du mot de passe."""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Les mots de passe ne correspondent pas."})
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer pour rafraîchir le token JWT."""
    
    refresh = serializers.CharField(required=True)


class LogoutSerializer(serializers.Serializer):
    """Serializer pour la déconnexion."""
    
    refresh = serializers.CharField(required=True)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le profil utilisateur."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
    
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance