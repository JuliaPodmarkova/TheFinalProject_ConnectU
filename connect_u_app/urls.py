# connect_u_app/urls.py

from django.urls import path
# Теперь этот импорт будет работать без ошибок!
from .views import pages, interactions, auth_views

urlpatterns = [
    # ========================
    # ОСНОВНЫЕ СТРАНИЦЫ
    # ========================
    path('', pages.index, name='home'),

    # ========================
    # ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
    # ========================
    path('profile/', pages.profile_own_view, name='profile_own'),
    path('profile/edit/', pages.profile_edit_view, name='profile_edit'),

    # ========================
    # ВЗАИМОДЕЙСТВИЯ (ЛАЙКИ/ДИЗЛАЙКИ)
    # ========================
    path('like/<int:pk>/', interactions.like_user_view, name='like_user'),
    path('dislike/<int:pk>/', interactions.dislike_user_view, name='dislike_user'),

    # ========================
    # АУТЕНТИФИКАЦИЯ (теперь все пути ведут в auth_views.py)
    # ========================
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    # 'signup/' - это адрес в браузере, 'register' - имя для Django
    path('signup/', auth_views.register_view, name='register'),
]