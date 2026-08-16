# servers/models.py
from django.db import models
from accounts.models import User
from django.utils.text import slugify

class Server(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_servers')
    members = models.ManyToManyField(User, through='ServerMember', related_name='servers')
    icon = models.ImageField(upload_to='server_icons/', blank=True, null=True)
    invite_code = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(max_length=500, blank=True)
    
    class Meta:
        verbose_name = 'Сервер'
        verbose_name_plural = 'Серверы'
    
    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = slugify(self.name)[:8] + str(self.id)[:4]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class ServerMember(models.Model):
    ROLES = [
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
        ('moderator', 'Модератор'),
        ('member', 'Участник'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    nickname = models.CharField(max_length=50, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'server')

class Category(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['position']
    
    def __str__(self):
        return f"{self.server.name} - {self.name}"

class Channel(models.Model):
    CHANNEL_TYPES = [
        ('text', 'Текстовый канал'),
        ('voice', 'Голосовой канал'),
    ]
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='channels')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='channels')
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPES, default='text')
    topic = models.CharField(max_length=500, blank=True)
    position = models.IntegerField(default=0)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"#{self.name}"