from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/voice/(?P<channel_id>\d+)/$', consumers.VoiceConsumer.as_asgi()),
]