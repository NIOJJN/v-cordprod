from django.db import models
from accounts.models import User
from servers.models import Channel

class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    attachments = models.FileField(upload_to='attachments/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"

class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    attachments = models.FileField(upload_to='dm_attachments/', blank=True, null=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"DM from {self.sender.username} to {self.recipient.username}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('friend_request', 'Запрос в друзья'),
        ('friend_accept', 'Запрос принят'),
        ('new_message', 'Новое сообщение'),
        ('server_invite', 'Приглашение на сервер'),
        ('mention', 'Упоминание'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"