from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from . import api


router = DefaultRouter()
router.register(r'profiles', api_views.ProfileViewSet, basename='profile')
router.register(r'users', api.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]