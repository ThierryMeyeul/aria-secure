from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentification
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa-verify'),
    path('mfa/setup/', views.MFASetupView.as_view(), name='mfa-setup'),
    path('mfa/enable/', views.MFAEnableView.as_view(), name='mfa-enable'),
    path('mfa/disable/', views.MFADisableView.as_view(), name='mfa-disable'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='token-refresh'),
    
    # Gestion du mot de passe
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # Admin
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<uuid:id>/', views.UserDetailView.as_view(), name='user-detail'),
]