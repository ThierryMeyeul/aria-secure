"""
Backends d'authentification personnalisés pour ARIA Secure.
Permet l'authentification par email plutôt que par username.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging
from datetime import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend d'authentification qui utilise l'email comme identifiant principal.
    Supporte également l'authentification avec MFA (vérification en deux étapes).
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie un utilisateur avec son email et mot de passe.
        
        Args:
            request: La requête HTTP (peut être None)
            username: L'email de l'utilisateur
            password: Le mot de passe en clair
            **kwargs: Arguments supplémentaires
            
        Returns:
            User object si authentification réussie, None sinon
        """
        if username is None or password is None:
            logger.debug("Authentification échouée: email ou mot de passe manquant")
            return None
        
        # Normaliser l'email (minuscules, sans espaces)
        email = username.strip().lower()
        
        try:
            # Rechercher l'utilisateur par email
            user = User.objects.get(email=email)
            
        except User.DoesNotExist:
            logger.debug(f"Tentative de connexion avec email inexistant: {email}")
            # Exécuter le setter de mot de passe pour éviter le timing attack
            User().set_password(password)
            return None
        
        # Vérifier le mot de passe
        if user.check_password(password):
            # Vérifier si le compte est actif
            if not user.is_active:
                logger.warning(f"Tentative de connexion sur compte inactif: {email}")
                return None
            
            logger.info(f"Authentification réussie pour: {email}")
            return user
        
        logger.debug(f"Mot de passe incorrect pour: {email}")
        return None
    
    def get_user(self, user_id):
        """
        Récupère un utilisateur par son ID.
        
        Args:
            user_id: L'identifiant UUID de l'utilisateur
            
        Returns:
            User object ou None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.debug(f"Utilisateur avec ID {user_id} non trouvé")
            return None


class EmailOrUsernameBackend(ModelBackend):
    """
    Backend d'authentification qui accepte soit l'email soit un nom d'utilisateur.
    Utile pour la phase de transition ou si on veut garder la flexibilité.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie un utilisateur avec email OU username.
        
        Args:
            request: La requête HTTP
            username: Email ou username
            password: Mot de passe
            
        Returns:
            User object ou None
        """
        if username is None or password is None:
            return None
        
        login_identifier = username.strip().lower()
        
        try:
            # Chercher par email OU par username (si le champ existe)
            user = User.objects.get(
                Q(email=login_identifier) | 
                Q(username=login_identifier)
            )
            
        except User.DoesNotExist:
            # Timing attack protection
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            logger.info(f"Authentification réussie pour: {login_identifier}")
            return user
        
        return None


class MFAEnabledBackend(ModelBackend):
    """
    Backend qui vérifie que l'utilisateur a complété la validation MFA.
    À utiliser en combinaison avec EmailBackend.
    """
    
    def authenticate(self, request, user=None, mfa_code=None, **kwargs):
        """
        Vérifie le code MFA après une première authentification réussie.
        
        Args:
            request: La requête HTTP
            user: L'utilisateur déjà authentifié (première étape)
            mfa_code: Le code TOTP à 6 chiffres
            **kwargs: Arguments supplémentaires
            
        Returns:
            User object si MFA valide, None sinon
        """
        if user is None or mfa_code is None:
            logger.debug("Vérification MFA échouée: utilisateur ou code manquant")
            return None
        
        # Vérifier que l'utilisateur a configuré MFA
        if not user.mfa_secret:
            logger.warning(f"Tentative MFA sans secret configuré pour: {user.email}")
            return None
        
        # Vérifier le code TOTP
        import pyotp
        
        totp = pyotp.TOTP(user.mfa_secret)
        
        # Vérifier avec une fenêtre de tolérance (±30 secondes)
        if totp.verify(mfa_code, valid_window=1):
            logger.info(f"Validation MFA réussie pour: {user.email}")
            return user
        
        logger.warning(f"Code MFA invalide pour: {user.email}")
        return None
    
    def get_user(self, user_id):
        """Récupère un utilisateur par son ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class TwoFactorBackend(ModelBackend):
    """
    Backend complet qui gère l'authentification en deux étapes.
    Combine la vérification email/password et MFA en une seule passe.
    """
    
    def authenticate(self, request, email=None, password=None, mfa_code=None, **kwargs):
        """
        Authentification complète avec MFA optionnel.
        
        Args:
            request: La requête HTTP
            email: Email de l'utilisateur
            password: Mot de passe
            mfa_code: Code MFA (optionnel, requis si l'utilisateur a MFA activé)
            
        Returns:
            User object si authentification complète réussie, None sinon
        """
        if email is None or password is None:
            return None
        
        email = email.strip().lower()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            User().set_password(password)
            return None
        
        # Vérifier le mot de passe d'abord
        if not user.check_password(password):
            logger.debug(f"Mot de passe incorrect pour: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Tentative sur compte inactif: {email}")
            return None
        
        # Si MFA n'est pas configuré pour cet utilisateur, on retourne directement
        if not user.mfa_secret:
            logger.info(f"Authentification réussie (sans MFA) pour: {email}")
            return user
        
        # Si MFA est configuré, le code est requis
        if mfa_code is None:
            logger.debug(f"Code MFA requis mais non fourni pour: {email}")
            return None
        
        # Vérifier le code MFA
        import pyotp
        totp = pyotp.TOTP(user.mfa_secret)
        
        if totp.verify(mfa_code, valid_window=1):
            logger.info(f"Authentification complète (avec MFA) réussie pour: {email}")
            return user
        
        logger.warning(f"Code MFA invalide pour: {email}")
        return None


class AuditLogBackend(ModelBackend):
    """
    Backend qui ajoute du logging d'audit pour toutes les tentatives d'authentification.
    Hérite de EmailBackend et ajoute des logs détaillés.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie avec logging d'audit.
        """
        from ipware import get_client_ip
        
        # Récupérer l'adresse IP
        client_ip, is_routable = get_client_ip(request) if request else (None, False)
        
        # Logger la tentative
        logger.info(
            f"Tentative d'authentification - Email: {username} - IP: {client_ip}"
        )
        
        # Authentification standard
        user = super().authenticate(request, username, password, **kwargs)
        
        if user:
            # Succès
            logger.info(
                f"Authentification RÉUSSIE - User: {user.email} - "
                f"Role: {user.role} - IP: {client_ip}"
            )
            
            # Mettre à jour last_login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        else:
            # Échec
            logger.warning(
                f"Authentification ÉCHOUÉE - Email: {username} - IP: {client_ip}"
            )
        
        return user