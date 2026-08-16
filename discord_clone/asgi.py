import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'discord_clone.settings')
django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns as chat_ws
from servers.routing import websocket_urlpatterns as server_ws
from voice.routing import websocket_urlpatterns as voice_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(URLRouter(chat_ws + server_ws + voice_ws)),
})