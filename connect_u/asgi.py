# connect_u/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import connect_u_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connect_u.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            connect_u_app.routing.websocket_urlpatterns
        )
    ),
})