from rest_framework import serializers
from .models import Patient, PatientAccess


class PatientSerializer(serializers.ModelSerializer):
    """Serializer principal pour le modèle Patient."""
    
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'record_number', 'first_name', 'last_name', 'birth_date',
            'gender', 'age', 'email', 'phone_number', 'adress',
            'created_by', 'created_by_email', 'created_by_name',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
    
    def get_age(self, obj):
        return obj.get_age()
    
    def validate_record_number(self, value):
        """Vérifie que le numéro de dossier est unique."""
        if Patient.objects.filter(record_number=value).exists():
            if self.instance and self.instance.record_number == value:
                return value
            raise serializers.ValidationError("This record number already exists.")
        return value


class PatientCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un patient."""
    
    class Meta:
        model = Patient
        fields = [
            'record_number', 'first_name', 'last_name', 'birth_date',
            'gender', 'email', 'phone_number', 'adress', 'notes'
        ]
    
    def validate_record_number(self, value):
        if Patient.objects.filter(record_number=value).exists():
            raise serializers.ValidationError("This record number already exists.")
        return value
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PatientUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un patient."""
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'birth_date', 'gender',
            'email', 'phone_number', 'adress', 'is_active', 'notes'
        ]


class PatientListSerializer(serializers.ModelSerializer):
    """Serializer léger pour lister les patients."""
    
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'record_number', 'first_name', 'last_name',
            'birth_date', 'gender', 'age', 'is_active', 'created_at'
        ]
    
    def get_age(self, obj):
        return obj.get_age()


class PatientAccessSerializer(serializers.ModelSerializer):
    """Serializer pour le journal d'accès patient."""
    
    accessed_by_email = serializers.EmailField(source='accessed_by.email', read_only=True)
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientAccess
        fields = [
            'id', 'patient', 'patient_name', 'accessed_by',
            'accessed_by_email', 'access_type', 'ip_address', 'created_at'
        ]
        read_only_fields = fields
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"