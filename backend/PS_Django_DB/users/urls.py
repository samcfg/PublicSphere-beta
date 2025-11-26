"""
URL routing for users app.
"""
from django.urls import path
from users.views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    UserProfileDetailView,
    UserContributionsView,
    UserContributionsListView,
    EntityAttributionView,
    ToggleAnonymityView,
    LeaderboardView,
    BatchAttributionView,
    UserDataExportView
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),

    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/<str:username>/', UserProfileDetailView.as_view(), name='profile-detail'),

    # Contributions
    path('contributions/', UserContributionsView.as_view(), name='contributions'),
    path('contributions/list/', UserContributionsListView.as_view(), name='contributions-list'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),

    # Attribution
    path('attribution/<str:entity_uuid>/', EntityAttributionView.as_view(), name='entity-attribution'),
    path('attributions/batch/', BatchAttributionView.as_view(), name='batch-attribution'),
    path('toggle-anonymity/', ToggleAnonymityView.as_view(), name='toggle-anonymity'),

    # Data export (GDPR)
    path('data/', UserDataExportView.as_view(), name='user-data-export'),
]
