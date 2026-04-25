from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.PatientListCreateView.as_view(), name='patient-list-create'),
    path('stats/', views.PatientStatsView.as_view(), name='patient-stats'),
    path('record/<str:record_number>/', views.PatientByRecordNumberView.as_view(), name='patient-by-record'),
    path('<uuid:id>/', views.PatientDetailView.as_view(), name='patient-detail'),
    path('<uuid:patient_id>/access-logs/', views.PatientAccessLogView.as_view(), name='patient-access-logs'),
]