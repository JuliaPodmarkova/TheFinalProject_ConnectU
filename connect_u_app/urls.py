from django.urls import path
from .views import pages, interactions, auth_views

urlpatterns = [
    path('', pages.index, name='home'),
    path('profile/', pages.profile_own_view, name='profile_own'),
    path('profile/edit/', pages.profile_edit_view, name='profile_edit'),
    path('like/<int:pk>/', interactions.like_user_view, name='like_user'),
    path('dislike/<int:pk>/', interactions.dislike_user_view, name='dislike_user'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('signup/', auth_views.register_view, name='register'),
    path('next/', interactions.show_next_user_view, name='show_next_user'),
]