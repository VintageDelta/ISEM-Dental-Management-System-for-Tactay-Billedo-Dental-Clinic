from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    profile_completed = models.BooleanField(default=False)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    
    password_reset_attempts = models.IntegerField(default=0)
    password_reset_locked_until = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def is_otp_valid(self):
        """Check if OTP is still valid (5 minutes)"""
        if not self.otp_created_at:
            return False
        
        # Calculate expiry time (5 minutes from creation)
        expiry_time = self.otp_created_at + timedelta(minutes=5)
        
        # Check if current time is before expiry
        return timezone.now() < expiry_time
    
    def is_password_reset_locked(self):
        """Check if account is locked due to too many failed OTP attempts"""
        if not self.password_reset_locked_until:
            return False
        
        # Check if lockout period has expired
        if timezone.now() >= self.password_reset_locked_until:
            # Lockout expired, auto-unlock the account
            self.password_reset_locked_until = None
            self.password_reset_attempts = 0
            self.save()
            return False
        
        # Still locked
        return True
    
    def get_lockout_time_remaining(self):
        """Get remaining lockout time in minutes"""
        if not self.password_reset_locked_until:
            return 0
        
        time_diff = self.password_reset_locked_until - timezone.now()
        minutes = int(time_diff.total_seconds() / 60)
        
        # Return 0 if time has passed, otherwise return remaining minutes
        return max(0, minutes)