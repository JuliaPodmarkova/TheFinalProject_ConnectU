import os
from django.core.asgi import get_asgi_application

# Сначала устанавливаем переменную окружения. Это критически важно.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connect_u.settings')

# Теперь мы вызываем get_asgi_application(), который инициализирует Django.
# После этой строки Django "готов".
django_asgi_app = get_asgi_application()

# И только теперь, когда Django готов, мы можем безопасно импортировать
# наши роутеры и консьюмеры, которые зависят от моделей.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import connect_u_app.routing

# Собираем наше итоговое приложение
application = ProtocolTypeRouter({
    "http": django_asgi_app, # Используем уже инициализированное приложение
    "websocket": AuthMiddlewareStack(
        URLRouter(
            connect_u_app.routing.websocket_urlpatterns
        )
    ),
})