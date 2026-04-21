from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.patients.models import Patient


class Radiography(BaseModel):
    """Radiographie médicale uploadée."""
    
    FORMAT_CHOICES = [
        ('DICOM', 'DICOM'),
        ('JPEG', 'JPEG'),
        ('PNG', 'PNG'),
    ]
    
    TYPE_CHOICES = [
    # Anatomie
    ('chest', 'Chest'),
    ('upper_limb', 'Upper Limb'),
    ('lower_limb', 'Lower Limb'),
    ('spine', 'Spine'),
    ('pelvis', 'Pelvis'),
    ('skull', 'Skull'),
    ('other', 'Other'),

    # MURA (musculoskeletal regions)
    ('elbow', 'Elbow'),
    ('finger', 'Finger'),
    ('forearm', 'Forearm'),
    ('hand', 'Hand'),
    ('humerus', 'Humerus'),
    ('shoulder', 'Shoulder'),
    ('wrist', 'Wrist'),

    # NIH ChestX-ray14 pathologies
    ('atelectasis', 'Atelectasis'),
    ('cardiomegaly', 'Cardiomegaly'),
    ('effusion', 'Pleural Effusion'),
    ('infiltration', 'Infiltration'),
    ('mass', 'Mass'),
    ('nodule', 'Nodule'),
    ('pneumonia', 'Pneumonia'),
    ('pneumothorax', 'Pneumothorax'),
    ('consolidation', 'Consolidation'),
    ('edema', 'Edema'),
    ('emphysema', 'Emphysema'),
    ('fibrosis', 'Fibrosis'),
    ('pleural_thickening', 'Pleural Thickening'),
    ('hernia', 'Hernia'),
]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='radiographies'
    )
    exam_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='thorax')
    image_format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    image_path = models.CharField(max_length=512)
    thumbnail_path = models.CharField(max_length=512, blank=True)
    taken_at = models.DateTimeField()
    quality_score = models.FloatField(null=True, blank=True)
    
    # Métadonnées DICOM (si applicable)
    dicom_metadata = models.JSONField(default=dict, blank=True)
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='radiographies_uploaded'
    )
    
    # Statut
    is_analyzed = models.BooleanField(default=False)
    analysis_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('processing', 'En cours'),
            ('completed', 'Terminée'),
            ('failed', 'Échouée'),
        ],
        default='pending'
    )
    
    class Meta:
        verbose_name = 'Radiographie'
        verbose_name_plural = 'Radiographies'
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['taken_at']),
            models.Index(fields=['analysis_status']),
            models.Index(fields=['uploaded_by']),
        ]
    
    def __str__(self):
        return f"Radio {self.patient.record_number} - {self.taken_at.date()}"
    
    def get_image_url(self):
        """Retourne l'URL signée pour accéder à l'image."""
        # Implémentation avec MinIO/S3
        pass
    
    def is_quality_sufficient(self):
        return self.quality_score and self.quality_score >= 0.3