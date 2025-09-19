# File: backend/apps/users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """
    Custom user manager to support username as unique identifier for authentication
    """
    def create_user(self, username, password=None, email=None, **extra_fields):
        """
        Creates and saves a User with the given username and password.
        Email is optional.
        """
        if not username:
            raise ValueError('The Username field must be set')

        user = self.model(username=username, **extra_fields)
        
        # Only set email if provided
        if email:
            user.email = self.normalize_email(email)
            
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, email=None, **extra_fields):
        """
        Creates and saves a superuser with the given username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, email, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses username as the primary identifier
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    )

    ACCOUNT_STATUS_CHOICES = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('deleted', 'Deleted'),
    )

    TWO_FACTOR_METHOD_CHOICES = (
        ('pin', 'PIN'),
        ('email', 'Email'),
        ('both', 'PIN and Email'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True, null=True)  # Made optional
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    date_joined = models.DateTimeField(default=timezone.now)
    reputation = models.IntegerField(default=0)
    last_login_timestamp = models.DateTimeField(null=True, blank=True)
    account_status = models.CharField(
        max_length=20, 
        choices=ACCOUNT_STATUS_CHOICES,
        default='active'
    )
    
    # 2FA Configuration
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=10,
        choices=TWO_FACTOR_METHOD_CHOICES,
        default='pin'
    )
    two_factor_pin = models.CharField(max_length=128, blank=True, null=True)  # User's chosen PIN

    # Required for Django's admin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    dark_mode_enabled = models.BooleanField(default=False)
    
    objects = UserManager()

    USERNAME_FIELD = 'username'  # Changed from 'email'
    REQUIRED_FIELDS = []  # Changed from ['username'] - email no longer required

    class Meta:
        ordering = ['-reputation']
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.username
    
    def get_full_name(self):
        return self.username
    
    def get_short_name(self):
        return self.username
    
    def set_pin(self, raw_pin):
        """Hash and set the 2FA PIN"""
        from django.contrib.auth.hashers import make_password
        self.two_factor_pin = make_password(raw_pin)
    
    def check_pin(self, raw_pin):
        """Check if the provided PIN matches the stored hash"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_pin, self.two_factor_pin)

    def has_pin_2fa(self):
        """Check if user has PIN-based 2FA enabled"""
        return (
            self.two_factor_enabled and 
            self.two_factor_pin and 
            self.two_factor_method in ['pin', 'both']
        )
    
    def has_email_2fa(self):
        """Check if user has email-based 2FA enabled"""
        return (
            self.two_factor_enabled and 
            self.email and 
            self.two_factor_method in ['email', 'both']
        )
    
    def verify_2fa(self, pin=None, email=None):
        """Verify 2FA credentials"""
        if not self.two_factor_enabled:
            return True  # No 2FA required
        
        # Check PIN if user has PIN 2FA
        if self.has_pin_2fa():
            if pin and self.check_pin(pin):
                return True
            elif self.two_factor_method == 'pin':
                return False  # PIN required but not provided/incorrect
        
        # Check email if user has email 2FA
        if self.has_email_2fa():
            if email and email.lower() == self.email.lower():
                return True
            elif self.two_factor_method == 'email':
                return False  # Email required but not provided/incorrect
        
        # For 'both' method, either PIN or email is sufficient
        return False


class UserConsent(models.Model):
    """
    Model to track user consent for various policies and terms
    """
    CONSENT_TYPE_CHOICES = (
        ('privacy_policy', 'Privacy Policy'),
        ('terms_of_service', 'Terms of Service'),
        ('cookies', 'Cookies'),
        ('marketing', 'Marketing'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='consents'
    )
    consent_type = models.CharField(
        max_length=20,
        choices=CONSENT_TYPE_CHOICES
    )
    consent_version = models.CharField(max_length=20)
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'consent_type', 'consent_version']
        verbose_name = 'user consent'
        verbose_name_plural = 'user consents'

    def __str__(self):
        status = "Granted" if not self.revoked_at else "Revoked"
        return f"{self.user.username} - {self.get_consent_type_display()} ({status})"

    def is_active(self):
        return self.revoked_at is None