# connect_u/asgi.py

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Устанавливаем переменную окружения с настройками.
# Это должно быть ДО любых других импортов Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connect_u.settings')

# <<< ✨ ВОТ ОНО, РЕШЕНИЕ! ✨ >>>
# Явно инициализируем Django и его реестр приложений.
# Теперь Django готов к работе с моделями.
django.setup()

# Теперь, когда Django загружен, мы можем безопасно импортировать
# наш роутинг, который в свою очередь импортирует consumers и модели.
import connect_u_app.routing

application = ProtocolTypeRouter({
    # HTTP-запросы по-прежнему обрабатываются стандартным приложением Django.
    "http": get_asgi_application(),

    # WebSocket-запросы обрабатываются нашим роутером.
    # AuthMiddlewareStack позволяет получить доступ к request.user в consumer'ах.
    "websocket": AuthMiddlewareStack(
        URLRouter(
            connect_u_app.routing.websocket_urlpatterns
        )
    ),
})