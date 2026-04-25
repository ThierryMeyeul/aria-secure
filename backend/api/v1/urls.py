from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Endpoint de vérification de santé simple."""
    return JsonResponse({
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'ARIA Secure API'
    })


urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('auth/', include('apps.authentication.urls')),
    path('patients/', include('apps.patients.urls')),
]