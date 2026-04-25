import django_filters
from django.db import models
from .models import Patient


class PatientFilter(django_filters.FilterSet):
    """Filtres pour la recherche de patients."""
    
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    record_number = django_filters.CharFilter(lookup_expr='icontains')
    gender = django_filters.ChoiceFilter(choices=Patient.GENDER_CHOICES)
    is_active = django_filters.BooleanFilter()
    
    birth_date_min = django_filters.DateFilter(
        field_name='birth_date',
        lookup_expr='gte'
    )
    birth_date_max = django_filters.DateFilter(
        field_name='birth_date',
        lookup_expr='lte'
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    search = django_filters.CharFilter(method='search_patient')
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'record_number', 'gender',
            'is_active', 'birth_date_min', 'birth_date_max',
            'created_after', 'created_before', 'search'
        ]
    
    def search_patient(self, queryset, name, value):
        """Recherche globale sur first_name, last_name et record_number."""
        return queryset.filter(
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value) |
            models.Q(record_number__icontains=value)
        )