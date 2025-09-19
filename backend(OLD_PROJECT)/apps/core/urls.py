#backend/apps/core/urls.py
from django.urls import path
from .views import ActiveBannersView

urlpatterns = [
    path('banners/', ActiveBannersView.as_view(), name='active-banners'),
]