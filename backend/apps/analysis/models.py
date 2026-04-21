from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.radiography.models import Radiography


class IAAnalysis(BaseModel):
    """Résultat d'analyse IA d'une radiographie."""
    
    radiography = models.OneToOneField(
        Radiography,
        on_delete=models.CASCADE,
        related_name='analyse'
    )
    model_version = models.CharField(max_length=50)
    results = models.JSONField(default=dict)
    heatmap_path = models.CharField(max_length=512, blank=True)
    duration_ms = models.IntegerField()
    
    # Métriques de confiance
    global_confidence = models.FloatField(null=True, blank=True)
    
    # Statut de validation
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente de validation'),
            ('validated', 'Validé par radiologue'),
            ('corrected', 'Corrigé par radiologue'),
            ('rejected', 'Rejeté'),
        ],
        default='pending'
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyses_validated'
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    validation_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Analyse IA'
        verbose_name_plural = 'Analyses IA'
        indexes = [
            models.Index(fields=['radiography']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Analyse {self.radiography.patient.record_number} - {self.created_at.date()}"
    
    def get_critical_pathologies(self):
        return self.pathologies.filter(is_critical=True)
    
    def has_critical_pathology(self):
        return self.pathologies.filter(is_critical=True).exists()


class Pathology(BaseModel):
    """Pathologie détectée par l'IA."""
    
    analysis = models.ForeignKey(
        IAAnalysis,
        on_delete=models.CASCADE,
        related_name='pathologies'
    )
    name = models.CharField(max_length=100)
    icd10_code = models.CharField(max_length=10, blank=True)
    confidence_score = models.FloatField()
    is_critical = models.BooleanField(default=False)
    
    # Localisation dans l'image
    localisation = models.JSONField(default=dict, blank=True)
    
    # Validation humaine
    is_validated = models.BooleanField(default=False)
    corrected_name = models.CharField(max_length=100, blank=True)
    correction_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Pathologie'
        verbose_name_plural = 'Pathologies'
        ordering = ['-confidence_score']
        indexes = [
            models.Index(fields=['analysis']),
            models.Index(fields=['name']),
            models.Index(fields=['is_critical']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.confidence_score:.0%}"
    
    def get_display_name(self):
        if self.is_validated and self.corrected_name:
            return self.corrected_name
        return self.name
    
    def get_confidence_level(self):
        if self.confidence_score >= 0.8:
            return 'high'
        elif self.confidence_score >= 0.5:
            return 'medium'
        return 'low'