from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views


router = DefaultRouter()
router.register(r'profiles', api_views.ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]