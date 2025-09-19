#backend/apps/core/serializers.py
from rest_framework import serializers
from .models import SiteBanner

class SiteBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteBanner
        fields = ['id', 'title', 'message', 'severity', 'is_dismissible', 'created_at']