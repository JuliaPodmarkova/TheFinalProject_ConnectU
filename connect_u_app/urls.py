from django.urls import path
from .views import pages, interactions, auth_views
from django.views.generic.base import RedirectView
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)

urlpatterns = [
    path('', pages.index, name='home'),
    path('profile/', pages.profile_own_view, name='profile_own'),
    path('profile/edit/', pages.profile_edit_view, name='profile_edit'),
    path('like/<int:pk>/', interactions.like_user_view, name='like_user'),
    path('dislike/<int:pk>/', interactions.dislike_user_view, name='dislike_user'),

    path('signup/', auth_views.register_view, name='signup'),

    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),

    path('next/', interactions.show_next_user_view, name='show_next_user'),

    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('accounts/logout/', RedirectView.as_view(url='/logout/', permanent=False)),
    path('accounts/signup/', RedirectView.as_view(url='/signup/', permanent=False)),
    path('api/v1/auth/jwt/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]