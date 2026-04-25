from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Patient(BaseModel):
    """Dossier patient avec anonymisation."""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    record_number = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Contact
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    adress = models.TextField(blank=True)
    
    # Métadonnées
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='patients_created'
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        indexes = [
            models.Index(fields=['record_number']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.record_number}"
    
    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    def get_display_name(self):
        """Version anonymisée pour les logs."""
        return f"Patient-{self.record_number}"


class PatientAccess(BaseModel):
    """Traçage des accès aux dossiers patients."""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='access_logs')
    accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='patient_accesses'
    )
    access_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Accès patient'
        verbose_name_plural = 'Accès patients'
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['accessed_by']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.accessed_by.email} → {self.patient.record_number} ({self.access_type})"