from rest_framework import viewsets, permissions
from .models import UserProfile
from .serializers import ProfileSerializer


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт, который позволяет просматривать профили пользователей.
    Доступно только чтение (GET-запросы).
    """
    queryset = UserProfile.objects.filter(
        searchable=True,
        user__is_active=True
    ).select_related('user').prefetch_related('interests')

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
