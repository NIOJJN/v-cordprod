from django.db import models
from accounts.models import User
from servers.models import Channel

class VoiceChannel(models.Model):
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name='voice_channel')
    connected_users = models.ManyToManyField(User, through='VoiceConnection')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def user_count(self):
        return self.connected_users.count()

class VoiceConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voice_channel = models.ForeignKey(VoiceChannel, on_delete=models.CASCADE)
    connected_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    is_deafened = models.BooleanField(default=False)
    is_speaking = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'voice_channel')