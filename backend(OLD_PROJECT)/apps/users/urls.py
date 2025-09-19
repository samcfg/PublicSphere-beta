# File: backend/apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'consents', views.UserConsentViewSet, basename='user-consent')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/check/', views.LoginCheckView.as_view(), name='login-check'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.UserDetailsView.as_view(), name='user-details'),
    path('2fa/setup/', views.TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    # GDPR:
    path('account-data/', views.AccountDataView.as_view(), name='account-data'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete-account'),
    path('preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
]