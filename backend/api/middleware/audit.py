"""
Middleware d'audit pour ARIA Secure.
Enregistre toutes les actions sensibles dans la base de données.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model

# Importer le modèle depuis l'application core
from apps.core.models import AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """
    Middleware pour enregistrer automatiquement les requêtes dans les logs d'audit.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('audit')
        
        # Configuration depuis settings
        self.enabled = getattr(settings, 'AUDIT_LOG_ENABLED', True)
        self.log_methods = getattr(settings, 'AUDIT_LOG_METHODS', ['POST', 'PUT', 'PATCH', 'DELETE'])
        self.exclude_paths = getattr(settings, 'AUDIT_LOG_EXCLUDE_PATHS', [
            '/admin/jsi18n/',
            '/api/v1/health/',
            '/api/v1/metrics/',
            '/static/',
            '/media/',
        ])
        self.include_get = getattr(settings, 'AUDIT_LOG_INCLUDE_GET', False)
        self.sensitive_fields = getattr(settings, 'AUDIT_LOG_SENSITIVE_FIELDS', [
            'password', 'token', 'secret', 'key', 'authorization',
            'access', 'refresh', 'otp_code', 'mfa_code'
        ])
        
    def __call__(self, request):
        # Ne pas logger si désactivé
        if not self.enabled:
            return self.get_response(request)
        
        # Vérifier si on doit logger cette requête
        should_log = self._should_log_request(request)
        
        # Capturer les données avant la requête
        request_data = None
        if should_log:
            request_data = self._capture_request_data(request)
        
        # Exécuter la vue
        response = self.get_response(request)
        
        # Logger après la réponse
        if should_log:
            self._log_request(request, response, request_data)
        
        return response
    
    def _should_log_request(self, request) -> bool:
        """Détermine si la requête doit être loggée."""
        # Vérifier le chemin
        path = request.path
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                return False
        
        # Vérifier la méthode HTTP
        method = request.method
        if method == 'GET' and not self.include_get:
            return False
        
        if method not in self.log_methods and method != 'GET':
            return False
        
        return True
    
    def _capture_request_data(self, request) -> Dict[str, Any]:
        """Capture les données de la requête de manière sécurisée."""
        data = {}
        
        # GET parameters
        if request.GET:
            data['query_params'] = self._sanitize_data(dict(request.GET))
        
        # POST/PUT/PATCH data
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.content_type == 'application/json':
                try:
                    body = json.loads(request.body.decode('utf-8'))
                    data['body'] = self._sanitize_data(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    data['body'] = '[Données binaires ou invalides]'
            elif request.POST:
                data['form_data'] = self._sanitize_data(dict(request.POST))
            
            # Fichiers uploadés
            if request.FILES:
                files_info = []
                for field_name, file_obj in request.FILES.items():
                    files_info.append({
                        'field': field_name,
                        'filename': file_obj.name,
                        'size': file_obj.size,
                        'content_type': file_obj.content_type
                    })
                data['files'] = files_info
        
        return data
    
    def _sanitize_data(self, data: Any) -> Any:
        """Nettoie les données sensibles avant de les logger."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Vérifier si la clé est sensible
                is_sensitive = any(
                    sensitive in key.lower() 
                    for sensitive in self.sensitive_fields
                )
                
                if is_sensitive:
                    sanitized[key] = '[MASQUÉ]'
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_data(value)
                else:
                    # Tronquer les longues valeurs
                    if isinstance(value, str) and len(value) > 500:
                        sanitized[key] = value[:500] + '... [TRONQUÉ]'
                    else:
                        sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data[:20]]
        else:
            if isinstance(data, str) and len(data) > 500:
                return data[:500] + '... [TRONQUÉ]'
            return data
    
    def _log_request(self, request, response, request_data: Optional[Dict]):
        """Enregistre la requête dans les logs d'audit."""
        try:
            # Déterminer l'action en fonction de la méthode HTTP
            action = self._determine_action(request)
            
            # Déterminer la ressource
            resource = self._determine_resource(request)
            resource_id = self._extract_resource_id(request)
            
            # Informations utilisateur
            user = None
            user_email = 'Anonyme'
            user_role = ''
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
                user_email = user.email
                user_role = getattr(user, 'role', '')
            
            # Créer le log d'audit
            audit_log = AuditLog(
                user=user,
                user_email=user_email,
                user_role=user_role,
                action=action,
                resource=resource,
                resource_id=resource_id,
                method=request.method,
                path=request.path,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                details={
                    'request_data': request_data,
                    'response_status': response.status_code,
                    'view_name': getattr(request, 'resolver_match', None) and request.resolver_match.view_name,
                },
                status_code=response.status_code,
            )
            
            audit_log.save()
            
            # Logger aussi dans les logs système
            self.logger.info(
                f"Audit: {user_email} - {action} - {resource} - {response.status_code}",
                extra={
                    'audit_log_id': audit_log.id,
                    'user': user_email,
                    'action': action,
                    'resource': resource,
                    'path': request.path,
                    'status': response.status_code,
                }
            )
            
        except Exception as e:
            # Ne pas bloquer l'application si l'audit échoue
            self.logger.error(f"Erreur lors de l'audit: {str(e)}", exc_info=True)
    
    def _determine_action(self, request) -> str:
        """Détermine le type d'action en fonction de la méthode et du chemin."""
        method = request.method
        path = request.path.lower()
        
        # Actions spéciales basées sur le chemin
        if 'login' in path:
            return 'LOGIN'
        elif 'logout' in path:
            return 'LOGOUT'
        elif 'mfa' in path and 'verify' in path:
            return 'MFA_VERIFY'
        elif 'mfa' in path and 'setup' in path:
            return 'MFA_SETUP'
        elif 'analyze' in path or 'analyse' in path:
            return 'ANALYZE'
        elif 'export' in path:
            return 'EXPORT'
        elif 'report' in path and 'sign' in path:
            return 'REPORT_SIGN'
        elif 'report' in path:
            return 'REPORT_GENERATE'
        
        # Actions basées sur la méthode HTTP
        method_actions = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE',
            'GET': 'VIEW',
        }
        
        return method_actions.get(method, 'VIEW')
    
    def _determine_resource(self, request) -> str:
        """Détermine le type de ressource à partir du chemin."""
        path = request.path.lower()
        parts = [p for p in path.split('/') if p]
        
        resource_mapping = {
            'patients': 'Patient',
            'radiographies': 'Radiographie',
            'analyses': 'Analyse',
            'analyses': 'Analyse',
            'rapports': 'Rapport',
            'users': 'Utilisateur',
            'auth': 'Authentification',
            'admin': 'Administration',
        }
        
        for part in parts:
            if part in resource_mapping:
                return resource_mapping[part]
        
        if len(parts) >= 3 and parts[0] == 'api' and parts[1] == 'v1':
            return parts[2].capitalize() if len(parts) > 2 else 'API'
        
        return 'Inconnu'
    
    def _extract_resource_id(self, request) -> str:
        """Extrait l'ID de la ressource de l'URL si présent."""
        import re
        
        # Pattern UUID
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, request.path)
        if uuid_match:
            return uuid_match.group()
        
        # Pattern ID numérique
        id_pattern = r'/(\d+)/'
        id_match = re.search(id_pattern, request.path)
        if id_match:
            return id_match.group(1)
        
        return ''
    
    def _get_client_ip(self, request) -> str:
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip


class AuditContextManager:
    """Gestionnaire de contexte pour logger manuellement des actions d'audit."""
    
    def __init__(self, user, action: str, resource: str, resource_id: str = ''):
        self.user = user
        self.action = action
        self.resource = resource
        self.resource_id = resource_id
        self.details = {}
        self.start_time = datetime.now()
        self.audit_log = None
        self.status_code = 200
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.status_code = 500
            self.add_detail('error', str(exc_val))
            self.add_detail('exception_type', exc_type.__name__)
        
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        self.add_detail('duration_ms', duration_ms)
        
        self._save()
        return False
    
    def add_detail(self, key: str, value: Any):
        """Ajoute une information au détail de l'audit."""
        self.details[key] = value
    
    def success(self):
        """Marque l'action comme réussie."""
        self.status_code = 200
    
    def failure(self, error_message: str):
        """Marque l'action comme échouée."""
        self.status_code = 500
        self.add_detail('error', error_message)
    
    def _save(self):
        """Sauvegarde le log d'audit."""
        try:
            self.audit_log = AuditLog.objects.create(
                user=self.user,
                user_email=self.user.email if self.user else '',
                user_role=getattr(self.user, 'role', '') if self.user else '',
                action=self.action,
                resource=self.resource,
                resource_id=self.resource_id,
                details=self.details,
                status_code=self.status_code,
            )
            
            logger.info(
                f"Audit manuel: {self.user.email if self.user else 'Système'} - {self.action} - {self.resource}",
                extra={'audit_log_id': self.audit_log.id}
            )
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde audit manuel: {e}")


def log_audit(user, action: str, resource: str, resource_id: str = '', **details):
    """Fonction utilitaire pour logger rapidement une action d'audit."""
    try:
        audit_log = AuditLog.objects.create(
            user=user,
            user_email=user.email if user else '',
            user_role=getattr(user, 'role', '') if user else '',
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            status_code=200,
        )
        
        logger.info(
            f"Audit: {user.email if user else 'Système'} - {action} - {resource}",
            extra={'audit_log_id': audit_log.id}
        )
        
        return audit_log
        
    except Exception as e:
        logger.error(f"Erreur fonction log_audit: {e}")
        return None


def setup_audit_logger():
    """Configure un logger spécifique pour l'audit."""
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    
    if not audit_logger.handlers:
        handler = logging.FileHandler('logs/audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        audit_logger.propagate = False
    
    return audit_logger


audit_logger = setup_audit_logger()