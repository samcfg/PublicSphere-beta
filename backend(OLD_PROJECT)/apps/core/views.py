#backend/apps/core/views.py
from rest_framework import generics
from django.utils import timezone
from django.db.models import Q
from .models import SiteBanner
from .serializers import SiteBannerSerializer

class ActiveBannersView(generics.ListAPIView):
    serializer_class = SiteBannerSerializer
    
    def get_queryset(self):
        now = timezone.now()
        return SiteBanner.objects.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )