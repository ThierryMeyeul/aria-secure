from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Patient, PatientAccess
from .serializers import (
    PatientSerializer, PatientCreateSerializer,
    PatientUpdateSerializer, PatientListSerializer,
    PatientAccessSerializer
)
from .permissions import IsOwnerOrAdmin, IsUserOrRadiologistOrAdmin, IsRadiologistOrAdmin
from .filters import PatientFilter


def log_patient_access(user, patient, access_type, request):
    """Enregistre un accès au dossier patient."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    PatientAccess.objects.create(
        patient=patient,
        accessed_by=user,
        access_type=access_type,
        ip_address=ip
    )


class PatientListCreateView(generics.ListCreateAPIView):
    """
    Lists all patients of the connected doctor.
    Creates a new patient.
    """
    
    permission_classes = [permissions.IsAuthenticated, IsUserOrRadiologistOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PatientFilter
    search_fields = ['first_name', 'last_name', 'record_number']
    ordering_fields = ['first_name', 'last_name', 'birth_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Patient.objects.all()
        return Patient.objects.filter(created_by=user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientCreateSerializer
        return PatientListSerializer
    
    def perform_create(self, serializer):
        patient = serializer.save()
        log_patient_access(self.request.user, patient, 'CREATE', self.request)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates or deactivates a patient.
    """
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Patient.objects.all()
        return Patient.objects.filter(created_by=user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PatientUpdateSerializer
        return PatientSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        log_patient_access(request.user, instance, 'VIEW', request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        patient = serializer.save()
        log_patient_access(self.request.user, patient, 'UPDATE', self.request)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        log_patient_access(self.request.user, instance, 'DELETE', self.request)


class PatientByRecordNumberView(generics.RetrieveAPIView):
    """
    Search a patient by their record number.
    """
    
    permission_classes = [permissions.IsAuthenticated, IsUserOrRadiologistOrAdmin]
    serializer_class = PatientSerializer
    lookup_field = 'record_number'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Patient.objects.all()
        return Patient.objects.filter(created_by=user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        log_patient_access(request.user, instance, 'VIEW', request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PatientAccessLogView(generics.ListAPIView):
    """
    Access log for a patient.
    """
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = PatientAccessSerializer
    
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        user = self.request.user
        
        queryset = PatientAccess.objects.filter(patient_id=patient_id)
        
        if user.is_superuser or user.role == 'admin':
            return queryset
        
        patient = Patient.objects.get(id=patient_id, created_by=user)
        return queryset


class PatientStatsView(generics.GenericAPIView):
    """
    Statistics on the connected doctor's patients.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.is_superuser or user.role == 'admin':
            patients = Patient.objects.all()
        else:
            patients = Patient.objects.filter(created_by=user)
        
        total = patients.count()
        active = patients.filter(is_active=True).count()
        
        by_gender = {
            'male': patients.filter(gender='M').count(),
            'female': patients.filter(gender='F').count(),
            'other': patients.filter(gender='O').count(),
        }
        
        today = timezone.now().date()
        this_week = patients.filter(created_at__date__gte=today - timezone.timedelta(days=7)).count()
        this_month = patients.filter(created_at__date__gte=today - timezone.timedelta(days=30)).count()
        
        return Response({
            'total': total,
            'active': active,
            'inactive': total - active,
            'by_gender': by_gender,
            'this_week': this_week,
            'this_month': this_month,
        })