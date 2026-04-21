from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.analysis.models import IAAnalysis
from apps.patients.models import Patient


class Report(BaseModel):
    """Rapport médical généré."""
    
    STATUT_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending_signature', 'En attente de signature'),
        ('signed', 'Signé'),
        ('archived', 'Archivé'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='reports'
    )
    analysis = models.OneToOneField(
        IAAnalysis,
        on_delete=models.PROTECT,
        related_name='reports'
    )
    
    # Contenu
    title = models.CharField(max_length=200)
    content = models.TextField()
    conclusions = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Fichiers
    pdf_path = models.CharField(max_length=512, blank=True)
    
    # Auteurs et signatures
    written_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reports_written'
    )
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_signed'
    )
    
    # Statut et dates
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='draft')
    signature_date = models.DateTimeField(null=True, blank=True)
    digital_signature = models.TextField(blank=True)
    
    # Partage
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_reports'
    )
    
    class Meta:
        verbose_name = 'Rapport'
        verbose_name_plural = 'Rapports'
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['statut']),
            models.Index(fields=['created_at']),
            models.Index(fields=['written_by']),
        ]
    
    def __str__(self):
        return f"Rapport {self.patient.record_number} - {self.created_at.date()}"
    
    def is_signed(self):
        return self.statut == 'signed' and self.signature_date is not None
    
    def can_be_signed_by(self, user):
        return user.role in ['user', 'radiologist', 'admin']
    
    def sign(self, user):
        if not self.can_be_signed_by(user):
            raise ValueError("User not authorized to sign this report.")
        
        from django.utils import timezone
        self.statut = 'signed'
        self.signed_by = user
        self.signature_date = timezone.now()
        self.save()