from django.urls import path
from .views import pages, interactions, auth_views, actions, swipe_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', pages.index, name='home'),
    path('search/', pages.search_view, name='search'),
    path('next/', interactions.show_next_user_view, name='show_next_user'),  #

    path('signup/', auth_views.register_view, name='signup'),
    path('logout/', auth_views.logout_view, name='logout'),

    path('profile/', pages.profile_own_view, name='profile_own'),
    path('profile/<int:user_id>/', pages.profile_view, name='profile_view'),

    path('profile/edit/', pages.profile_edit_view, name='profile_edit'),
    path('profile/photos/', pages.profile_photos_view, name='profile_photos'),

    path('photo/<int:photo_id>/delete/', actions.delete_photo_view, name='delete_photo'),
    path('photo/<int:photo_id>/set_main/', actions.set_main_photo_view, name='set_main_photo'),
    path('like/<int:pk>/', interactions.like_user_view, name='like_user'),
    path('dislike/<int:pk>/', interactions.dislike_user_view, name='dislike_user'),

    path('matches/', pages.match_list_view, name='match_list'),
    path('chat/<int:match_id>/', pages.chat_view, name='chat'),

    path('gallery/', pages.photo_gallery_view, name='photo_gallery'),

    path('swipe/', swipe_views.swipe_view, name='swipe'),
    path('swipe/process/', swipe_views.swipe_view, name='process_swipe'),


    path('api/v1/auth/jwt/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]