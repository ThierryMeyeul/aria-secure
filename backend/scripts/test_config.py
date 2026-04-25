#!/usr/bin/env python
# backend/scripts/test_config.py
"""
Script pour tester la configuration Django.
À exécuter avec: python manage.py shell < scripts/test_config.py
Ou: python manage.py runscript test_config
"""

import os
import sys
import django

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aria_backend.settings.development')
django.setup()

from django.conf import settings
from django.core.management import call_command


def test_settings():
    """Teste la configuration Django."""
    print("\n" + "="*60)
    print("TEST DE CONFIGURATION DJANGO - ARIA SECURE")
    print("="*60)
    
    # 1. Environnement
    print(f"\n1. Environnement : {os.getenv('DJANGO_ENVIRONMENT', 'development')}")
    print(f"   DEBUG : {settings.DEBUG}")
    print(f"   SECRET_KEY : {'Définie' if settings.SECRET_KEY else 'MANQUANTE !!!'}")
    
    # 2. Base de données
    print(f"\n2. Base de données :")
    print(f"   Engine : {settings.DATABASES['default']['ENGINE']}")
    print(f"   Name : {settings.DATABASES['default'].get('NAME', 'N/A')}")
    
    # 3. Applications installées
    print(f"\n3. Applications installées : {len(settings.INSTALLED_APPS)}")
    for app in settings.INSTALLED_APPS:
        if app.startswith('apps.'):
            print(f"   ✓ {app}")
    
    # 4. Middleware
    print(f"\n4. Middleware : {len(settings.MIDDLEWARE)}")
    
    # 5. REST Framework
    print(f"\n5. REST Framework :")
    print(f"   Auth classes : {len(settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'])}")
    print(f"   Page size : {settings.REST_FRAMEWORK.get('PAGE_SIZE', 'N/A')}")
    
    # 6. JWT Settings
    print(f"\n6. JWT Settings :")
    print(f"   Access token : {settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']}")
    print(f"   Refresh token : {settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']}")
    print(f"   Algorithm : {settings.SIMPLE_JWT['ALGORITHM']}")
    
    # 7. Stockage
    print(f"\n7. Stockage :")
    print(f"   Media root : {settings.MEDIA_ROOT}")
    print(f"   Static root : {settings.STATIC_ROOT}")
    print(f"   MinIO : {settings.MINIO_ENDPOINT}")
    
    # 8. Celery
    print(f"\n8. Celery :")
    print(f"   Broker : {settings.CELERY_BROKER_URL}")
    print(f"   Always eager : {getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)}")
    
    # 9. Features
    print(f"\n9. Features activées :")
    for feature, enabled in settings.FEATURES.items():
        status = "✓" if enabled else "✗"
        print(f"   {status} {feature}")
    
    # 10. Sécurité
    print(f"\n10. Sécurité :")
    print(f"   SSL Redirect : {settings.SECURE_SSL_REDIRECT}")
    print(f"   HSTS : {settings.SECURE_HSTS_SECONDS}s")
    print(f"   CORS origins : {len(settings.CORS_ALLOWED_ORIGINS)}")
    
    # 11. Email
    print(f"\n11. Email :")
    print(f"   Backend : {settings.EMAIL_BACKEND}")
    print(f"   From : {settings.DEFAULT_FROM_EMAIL}")
    
    # 12. Logging
    print(f"\n12. Logging :")
    print(f"   Handlers : {list(settings.LOGGING['handlers'].keys())}")
    
    print("\n" + "="*60)
    print("✅ TEST TERMINÉ")
    print("="*60)


def test_database_connection():
    """Teste la connexion à la base de données."""
    from django.db import connection
    
    print("\n" + "="*60)
    print("TEST DE CONNEXION À LA BASE DE DONNÉES")
    print("="*60)
    
    try:
        connection.ensure_connection()
        print("✅ Connexion réussie !")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"   Test query : {result}")
            
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")


def test_migrations():
    """Vérifie les migrations en attente."""
    print("\n" + "="*60)
    print("VÉRIFICATION DES MIGRATIONS")
    print("="*60)
    
    try:
        call_command('showmigrations', '--plan')
    except Exception as e:
        print(f"❌ Erreur : {e}")


def test_create_superuser():
    """Vérifie si un superuser existe."""
    from django.contrib.auth import get_user_model
    
    print("\n" + "="*60)
    print("VÉRIFICATION SUPERUSER")
    print("="*60)
    
    User = get_user_model()
    superusers = User.objects.filter(is_superuser=True)
    
    if superusers.exists():
        print(f"✅ Superusers trouvés : {superusers.count()}")
        for user in superusers:
            print(f"   - {user.email}")
    else:
        print("⚠ Aucun superuser trouvé")
        print("   Créez-en un avec : python manage.py createsuperuser")


if __name__ == '__main__':
    test_settings()
    test_database_connection()
    test_create_superuser()
    
    print("\n📝 Commandes utiles :")
    print("   python manage.py runserver")
    print("   python manage.py makemigrations")
    print("   python manage.py migrate")
    print("   python manage.py createsuperuser")