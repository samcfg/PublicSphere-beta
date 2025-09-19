#backend/apps/core/admin.py
from django.contrib import admin
from .models import SiteBanner

@admin.register(SiteBanner)
class SiteBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'is_active', 'expires_at', 'created_at']
    list_filter = ['severity', 'is_active', 'created_at']
    search_fields = ['title', 'message']
    actions = ['activate_banners', 'deactivate_banners']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new banner
            obj.created_by = request.user
        super().save_model(request, obj, form, change)