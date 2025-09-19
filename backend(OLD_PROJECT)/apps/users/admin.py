# File: backend/apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserConsent

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model"""
    list_display = ('username', 'email', 'role', 'reputation', 'date_joined', 
                   'last_login_timestamp', 'account_status', 'is_active')
    list_filter = ('role', 'account_status', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login_timestamp')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('reputation',)}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'account_status'),
        }),
        (_('Security'), {'fields': ('two_factor_enabled', 'two_factor_method')}),
        (_('Important dates'), {'fields': ('date_joined', 'last_login_timestamp')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff'),
        }),
    )


@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    """Admin interface for UserConsent model"""
    list_display = ('user', 'consent_type', 'consent_version', 'granted_at', 'revoked_at')
    list_filter = ('consent_type', 'consent_version', 'granted_at', 'revoked_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('granted_at',)
    raw_id_fields = ('user',)