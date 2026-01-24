from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
