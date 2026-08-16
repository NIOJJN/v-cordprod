# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from PIL import Image
import os

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    status = models.CharField(max_length=20, choices=[
        ('online', 'Онлайн'),
        ('idle', 'Не активен'),
        ('dnd', 'Не беспокоить'),
        ('offline', 'Офлайн')
    ], default='offline')
    custom_status = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    friends = models.ManyToManyField('self', through='Friendship', symmetrical=False)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)
    
    def is_online(self):
        return self.status == 'online'

class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='friendship_from', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friendship_to', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        
class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)