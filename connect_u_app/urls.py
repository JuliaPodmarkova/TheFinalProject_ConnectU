from django.urls import path
from .views import pages, interactions, auth_views, actions, swipe_views

urlpatterns = [
    # Главная страница ведет на свайпы
    path('feed/', pages.home_view, name='feed'),
    path('', swipe_views.swipe_main_view, name='home'),

    # --- Профили и страницы ---
    path('profile/me/', pages.profile_own_view, name='profile_own'),
    path('profile/edit/', auth_views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', pages.profile_view, name='profile_view'),
    path('search/', pages.search_view, name='search'),
    path('matches/', pages.match_list_view, name='match_list'),
    path('chat/<int:match_id>/', pages.chat_view, name='chat'),
    path('photos/', pages.profile_photos_view, name='profile_photos'),
    path('photos/delete/<int:photo_id>/', actions.delete_photo_view, name='delete_photo'),
    path('photos/set_main/<int:photo_id>/', actions.set_main_photo_view, name='set_main_photo'),
    path('activity/', pages.activity_history_view, name='activity_history'),

    # --- Аутентификация ---
    path('accounts/login/', auth_views.login_view, name='account_login'),
    path('accounts/logout/', auth_views.logout_view, name='account_logout'),
    path('accounts/signup/', auth_views.register_view, name='account_signup'),
    path('close-popup/', pages.close_popup_view, name='close_popup'),

    # --- API для свайпов ---
    path('api/get_next_profile/', swipe_views.get_next_profile, name='get_next_profile'),
    path('api/swipe/', swipe_views.swipe, name='swipe_action'),

    # --- Взаимодействия (лайки/дизлайки из других мест, если нужны) ---
    path('like/<int:user_id>/', interactions.like_user_view, name='like_user'),
    path('dislike/<int:user_id>/', interactions.dislike_user_view, name='dislike_user'),

    # ИСПРАВЛЕНИЕ: Добавлены недостающие маршруты для приглашений
    path('invitation/send/<int:match_id>/', actions.send_invitation, name='send_invitation'),
    path('invitation/handle/<int:invitation_id>/', actions.handle_invitation, name='handle_invitation'),
]