from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow only the patient's creator or an admin.
    A doctor sees their own patients, an admin sees everything.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        
        return obj.created_by == request.user


class CanAccessPatient(permissions.BasePermission):
    """
    Permission to check access to a patient record.
    """
    
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        
        return obj.created_by == request.user


class IsUserOrRadiologistOrAdmin(permissions.BasePermission):
    """
    Permission to limit access to medical roles.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        
        return request.user.role in ['user', 'radiologist']


class IsRadiologistOrAdmin(permissions.BasePermission):
    """
    Permission for actions reserved to radiologists and admins.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        
        return request.user.role == 'radiologist'