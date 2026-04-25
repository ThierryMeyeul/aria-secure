# backend/aria_backend/settings/development.py
"""
Configuration Django pour l'environnement de développement.
"""
import sys
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '10.0.2.2', '*']

# Database - SQLite pour le développement local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'aria_db'),
        'USER': os.getenv('DB_USER', 'aria_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Utiliser SQLite en mémoire pour les tests plus rapides
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar', 'django_extensions', 'silk']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')

INTERNAL_IPS = ['127.0.0.1', 'localhost']

def show_toolbar(request):
    return True

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

# Silk profiling
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_AUTHENTICATION = False
SILKY_AUTHORISATION = False

# CORS - Permettre toutes les origines en dev
CORS_ALLOW_ALL_ORIGINS = True

# Désactiver certaines sécurités en dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# # Logging plus verbeux en développement
# LOGGING['loggers']['django.db.backends'] = {
#     'handlers': [],
#     'level': 'ERROR',
#     'propagate': False,
# }

# Celery - Exécution synchrone pour simplifier le dev
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Cache - Utiliser le cache local pour le dev
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Désactiver la protection CSRF pour les tests API en dev
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
    'rest_framework.authentication.SessionAuthentication'
)

# Plus petite durée de vie des tokens en dev pour tester les refresh
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)

# Désactiver Axes en dev pour éviter les blocages
AXES_ENABLED = False

# Email - Utiliser un vrai serveur SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aria-secure.com')