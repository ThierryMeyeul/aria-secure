# apps/core/models.py

from django.db import models
from django.conf import settings
import uuid


class BaseModel(models.Model):
    """Modèle abstrait de base avec timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class AuditLog(models.Model):
    """
    Modèle pour stocker les logs d'audit.
    """
    
    ACTION_TYPES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('LOGIN_FAILED', 'Échec de connexion'),
        ('MFA_VERIFY', 'Vérification MFA'),
        ('MFA_SETUP', 'Configuration MFA'),
        ('EXPORT', 'Export'),
        ('ANALYZE', 'Analyse IA'),
        ('REPORT_GENERATE', 'Génération rapport'),
        ('REPORT_SIGN', 'Signature rapport'),
        ('PERMISSION_DENIED', 'Accès refusé'),
        ('API_KEY', 'Utilisation clé API'),
    ]
    
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(blank=True)
    user_role = models.CharField(max_length=20, blank=True)
    
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    resource = models.CharField(max_length=200)
    resource_id = models.CharField(max_length=100, blank=True)
    
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    details = models.JSONField(default=dict, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp']),
            models.Index(fields=['resource', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user_email or 'Anonyme'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_str} - {self.action} - {self.resource}"