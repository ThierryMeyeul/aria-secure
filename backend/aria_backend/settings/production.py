# backend/aria_backend/settings/production.py
"""
Configuration Django pour l'environnement de production.
"""

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import ssl

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'aria_db'),
        'USER': os.getenv('DB_USER', 'aria_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Activer le pooling de connexions
DATABASES['default']['CONN_MAX_AGE'] = 600

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files - Utiliser S3/MinIO en production
if os.getenv('USE_S3_STORAGE', 'False').lower() == 'true':
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'eu-west-1')
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"

# Email - Utiliser un vrai serveur SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Cache - Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_CACHE_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.getenv('REDIS_PASSWORD'),
            'SSL': True,
        }
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery - Configuré pour Redis avec SSL si nécessaire
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': ssl.CERT_REQUIRED}

# Sentry
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
        send_default_pii=False,
    )

# Logging - Plus strict en production
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'INFO'

# Axes - Activer la protection
AXES_ENABLED = True
AXES_FAILURE_LIMIT = int(os.getenv('AXES_FAILURE_LIMIT', 5))
AXES_COOLOFF_TIME = timedelta(minutes=int(os.getenv('AXES_COOLOFF_MINUTES', 15)))

# Rate limiting plus strict
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10/minute',
    'user': '30/minute',
    'auth': '3/minute',
    'mfa': '5/minute',
}

print(f"✅ Configuration PRODUCTION chargée")
print(f"   DEBUG: {DEBUG}")
print(f"   Database: PostgreSQL")
print(f"   Sentry: {'Enabled' if os.getenv('SENTRY_DSN') else 'Disabled'}")