# backend/aria_backend/settings/base.py
"""
Configuration Django de base pour ARIA Secure.
Commune à tous les environnements.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import json

# Charger les variables d'environnement
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============================================
# CORE DJANGO SETTINGS
# ============================================

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'storages',
    'django_celery_beat',
    'django_celery_results',
    'health_check',
    # 'health_check.db',
    # 'health_check.cache',
    # 'health_check.storage',
    # 'health_check.contrib.migrations',
    # 'health_check.contrib.redis',
    'drf_spectacular',
    'axes',  # Protection brute force
]

LOCAL_APPS = [
    'apps.core',
    'apps.authentication',
    'apps.patients',
    'apps.radiography',
    'apps.analysis',
    'apps.reports',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # Doit être après AuthenticationMiddleware
    'api.middleware.audit.AuditLogMiddleware',
]

ROOT_URLCONF = 'aria_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aria_backend.wsgi.application'
ASGI_APPLICATION = 'aria_backend.asgi.application'

# ============================================
# AUTHENTICATION
# ============================================

AUTH_USER_MODEL = 'authentication.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Pour axes (rate limiting)
    'apps.authentication.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    # {'NAME': 'apps.authentication.validators.SpecialCharacterValidator'},
    # {'NAME': 'apps.authentication.validators.UppercaseLowercaseValidator'},
]

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# ============================================
# REST FRAMEWORK
# ============================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'apps.core.renderers.CustomJSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '60/minute',
        'auth': '5/minute',
        'mfa': '10/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================
# JWT SETTINGS
# ============================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

with open("/home/meyeul/private.pem") as f:
    SIGNING_KEY = f.read()

with open("/home/meyeul/public.pem") as f:
    VERIFYING_KEY = f.read()

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 30))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': os.getenv('JWT_ALGORITHM', 'RS256'),
    'SIGNING_KEY': os.getenv('ALGORITHM_SIGNING_KEY'),  # Sera configuré selon l'algorithme
    'VERIFYING_KEY': os.getenv('ALGORITHM_VERIFYING_KEY'),  # Sera configuré selon l'algorithme
    'AUDIENCE': 'aria-secure',
    'ISSUER': 'ARIA Secure',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
}

# ============================================
# INTERNATIONALIZATION
# ============================================

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ============================================
# STATIC & MEDIA FILES
# ============================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Whitenoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================
# STOCKAGE (MinIO / S3)
# ============================================

DEFAULT_FILE_STORAGE = 'apps.radiographies.storage.SecureStorage'

# MinIO Configuration
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'aria-secure')
MINIO_USE_SSL = os.getenv('MINIO_USE_SSL', 'False').lower() == 'true'

# ============================================
# CELERY
# ============================================

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/2')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ============================================
# CACHE
# ============================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_CACHE_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ============================================
# SECURITY
# ============================================

# HTTPS Settings
SECURE_SSL_REDIRECT = False  # Activé en production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Session & CSRF
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# ============================================
# CORS
# ============================================

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]

# ============================================
# AXES (Brute Force Protection)
# ============================================

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ACCESS_FAILURE_LOG = True

# ============================================
# LOGGING
# ============================================

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {asctime} {message}',
#             'style': '{',
#         },
#         'json': {
#             'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
#         },
#     },
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse',
#         },
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#             'filters': ['require_debug_true'],
#         },
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.getenv('LOG_DIR', '/var/log/aria-secure') + '/django.log',
#             'maxBytes': 10485760,  # 10 MB
#             'backupCount': 10,
#             'formatter': 'json',
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'class': 'django.utils.log.AdminEmailHandler',
#             'filters': ['require_debug_false'],
#         },
#         'sentry': {
#             'level': 'ERROR',
#             'class': 'sentry_sdk.integrations.logging.EventHandler',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#         'django.request': {
#             'handlers': ['mail_admins', 'sentry'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#         'django.security': {
#             'handlers': ['mail_admins', 'sentry'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#         'apps': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
# }

# ============================================
# AI MODEL SETTINGS
# ============================================

AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', BASE_DIR / 'ai_models' / 'aria_model.onnx')
AI_MODEL_VERSION = os.getenv('AI_MODEL_VERSION', 'v1.0.0')
AI_INFERENCE_TIMEOUT = int(os.getenv('AI_INFERENCE_TIMEOUT_SECONDS', 10))

# ============================================
# FEATURE FLAGS
# ============================================

FEATURES = {
    'MFA_ENABLED': os.getenv('FEATURE_MFA_ENABLED', 'True').lower() == 'true',
    'OFFLINE_MODE': os.getenv('FEATURE_OFFLINE_MODE', 'True').lower() == 'true',
    'AUDIT_LOG': os.getenv('FEATURE_AUDIT_LOG', 'True').lower() == 'true',
    'REPORT_SIGNATURE': os.getenv('FEATURE_REPORT_SIGNATURE', 'True').lower() == 'true',
}

# ============================================
# API DOCUMENTATION (drf-spectacular)
# ============================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'ARIA Secure API',
    'DESCRIPTION': 'API pour l\'analyse sécurisée de radiographies médicales',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {'name': 'ARIA Secure Support', 'email': 'support@aria-secure.com'},
    'LICENSE': {'name': 'Proprietary'},
    'SECURITY': [{'BearerAuth': []}],
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    'TAGS': [
        {'name': 'Authentication', 'description': 'Authentification et gestion des sessions'},
        {'name': 'Patients', 'description': 'Gestion des dossiers patients'},
        {'name': 'Radiographies', 'description': 'Upload et gestion des radiographies'},
        {'name': 'Analyses', 'description': 'Analyses IA et résultats'},
        {'name': 'Rapports', 'description': 'Génération de rapports médicaux'},
    ],
}

# ============================================
# AUDIT LOG
# ============================================

AUDIT_LOG_ENABLED = True
AUDIT_LOG_ACTIONS = ['CREATE', 'UPDATE', 'DELETE', 'VIEW', 'LOGIN', 'LOGOUT', 'EXPORT', 'ANALYZE']
AUDIT_LOG_INCLUDE_GET = False
AUDIT_LOG_EXCLUDE_PATHS = [
    '/admin/jsi18n/',
    '/api/v1/health/',
    '/static/',
    '/media/',
]
AUDIT_LOG_SENSITIVE_FIELDS = [
    'password', 'token', 'secret', 'key', 'authorization',
    'access', 'refresh', 'otp_code', 'mfa_code'
]

# ============================================
# EMAIL
# ============================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aria-secure.com')
ADMINS = [('Admin', os.getenv('ADMIN_EMAIL', 'admin@aria-secure.com'))]

# ============================================
# DEFAULT AUTO FIELD
# ============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'