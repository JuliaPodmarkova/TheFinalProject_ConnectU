# connect_u/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Путь для админки
    path('admin/', admin.site.urls),

    # Подключаем все URL-адреса из нашего приложения connect_u_app
    # Теперь '' (главная страница) будет обрабатываться там
    path('', include('connect_u_app.urls')),

    # URL для авторизации через соцсети (добавим позже, но пусть уже будет)
    path('oauth/', include('social_django.urls', namespace='social')),
    path('', include('django.contrib.auth.urls')),
]

# Этот блок нужен для того, чтобы в режиме разработки (DEBUG=True)
# Django мог сам раздавать загруженные медиафайлы.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)