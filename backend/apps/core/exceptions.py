"""
Exceptions personnalisées pour l'API ARIA Secure.
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class BaseAPIException(APIException):
    """Exception de base pour toutes les erreurs personnalisées de l'API."""
    
    default_detail = 'Une erreur est survenue.'
    default_code = 'error'
    
    def __init__(self, detail=None, code=None, status_code=None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class AuthenticationError(BaseAPIException):
    """Exception pour les erreurs d'authentification."""
    
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentification requise.'
    default_code = 'authentication_error'


class InvalidCredentialsError(BaseAPIException):
    """Exception pour les identifiants invalides."""
    
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Email ou mot de passe incorrect.'
    default_code = 'invalid_credentials'


class MFARequiredError(BaseAPIException):
    """Exception quand la vérification MFA est requise."""
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Vérification MFA requise.'
    default_code = 'mfa_required'


class InvalidMFAError(BaseAPIException):
    """Exception pour un code MFA invalide."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Code MFA invalide.'
    default_code = 'invalid_mfa'


class PermissionDeniedError(BaseAPIException):
    """Exception pour les accès non autorisés."""
    
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Vous n\'avez pas les permissions nécessaires.'
    default_code = 'permission_denied'


class ResourceNotFoundError(BaseAPIException):
    """Exception pour les ressources non trouvées."""
    
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Ressource non trouvée.'
    default_code = 'not_found'


class ValidationError(BaseAPIException):
    """Exception pour les erreurs de validation."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Données invalides.'
    default_code = 'validation_error'


class ConflictError(BaseAPIException):
    """Exception pour les conflits (ex: doublon)."""
    
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflit avec une ressource existante.'
    default_code = 'conflict'


class RateLimitExceededError(BaseAPIException):
    """Exception pour les limites de requêtes dépassées."""
    
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Trop de requêtes. Veuillez réessayer plus tard.'
    default_code = 'rate_limit_exceeded'


class ServiceUnavailableError(BaseAPIException):
    """Exception pour les services indisponibles."""
    
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporairement indisponible.'
    default_code = 'service_unavailable'


class AIAnalysisError(BaseAPIException):
    """Exception pour les erreurs d'analyse IA."""
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Erreur lors de l\'analyse IA.'
    default_code = 'ai_analysis_error'


class InvalidImageFormatError(BaseAPIException):
    """Exception pour les formats d'image non supportés."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Format d\'image non supporté. Utilisez DICOM, JPEG ou PNG.'
    default_code = 'invalid_image_format'


class ImageQualityError(BaseAPIException):
    """Exception pour les images de qualité insuffisante."""
    
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Qualité d\'image insuffisante pour l\'analyse.'
    default_code = 'image_quality_error'


class ReportGenerationError(BaseAPIException):
    """Exception pour les erreurs de génération de rapport."""
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Erreur lors de la génération du rapport.'
    default_code = 'report_generation_error'


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour l'API REST.
    Formate toutes les erreurs dans un format standardisé.
    """
    
    response = exception_handler(exc, context)
    
    if response is not None:
        view = context.get('view')
        request = context.get('request')
        
        logger.error(
            f"Exception in {view.__class__.__name__}: {exc}",
            exc_info=True,
            extra={
                'user': request.user.email if request and request.user.is_authenticated else 'anonymous',
                'path': request.path if request else None,
                'method': request.method if request else None,
            }
        )
        
        custom_response_data = {
            'success': False,
            'error': response.data,
            'status_code': response.status_code
        }
        
        response.data = custom_response_data
    
    return response