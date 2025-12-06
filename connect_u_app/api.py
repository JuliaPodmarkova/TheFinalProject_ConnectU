# connect_u_app/api.py

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

# Импортируем все необходимые модели
from .models import (
    User,
    UserProfile,
    Photo,
    Interaction,
    Match,
    Like,
    Dislike
)

# Импортируем все сериализаторы, которые мы определили
from .serializers import (
    UserProfileSerializer,
    UserSerializer,
    PhotoSerializer,
    InteractionSerializer,
    MatchSerializer,
)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API для управления профилем ТЕКУЩЕГО пользователя.
    Позволяет просматривать и редактировать свой собственный профиль.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Этот метод гарантирует, что пользователь видит и редактирует ТОЛЬКО свой профиль
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для просмотра ДРУГИХ пользователей и взаимодействия с ними (лайки/дизлайки).
    """
    queryset = User.objects.all().exclude(is_staff=True, is_superuser=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Исключаем текущего пользователя из списка, чтобы он не видел сам себя
        return super().get_queryset().exclude(pk=self.request.user.pk)

    @action(detail=True, methods=['post'], url_path='like')
    def like_user(self, request, pk=None):
        """
        Ставит лайк пользователю с ID={pk}.
        Возвращает {'status': 'like set', 'match': True/False}.
        """
        current_user = request.user
        liked_user = get_object_or_404(User, pk=pk)

        if current_user == liked_user:
            return Response({'error': 'You cannot like yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем лайк
        Like.objects.get_or_create(from_user=current_user, to_user=liked_user)

        # Проверяем, случился ли мэтч
        is_match = Like.objects.filter(from_user=liked_user, to_user=current_user).exists()

        if is_match:
            # Создаем мэтч, убедившись, что user1 < user2 по ID
            user_a, user_b = sorted([current_user, liked_user], key=lambda u: u.id)
            Match.objects.get_or_create(user1=user_a, user2=user_b)

        return Response({'status': 'like set', 'match': is_match}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='dislike')
    def dislike_user(self, request, pk=None):
        """
        Ставит дизлайк пользователю с ID={pk}.
        """
        current_user = request.user
        disliked_user = get_object_or_404(User, pk=pk)

        if current_user == disliked_user:
            return Response({'error': 'You cannot dislike yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        Dislike.objects.get_or_create(from_user=current_user, to_user=disliked_user)

        return Response({'status': 'dislike set'}, status=status.HTTP_200_OK)


class PhotoViewSet(viewsets.ModelViewSet):
    """
    API для управления фотографиями ТЕКУЩЕГО пользователя.
    """
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои фотографии
        return Photo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # При создании фото, оно автоматически привязывается к текущему пользователю
        serializer.save(user=self.request.user)


class InteractionViewSet(viewsets.ModelViewSet):
    """
    API для просмотра взаимодействий ТЕКУЩЕГО пользователя.
    """
    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои исходящие взаимодействия
        return Interaction.objects.filter(from_user=self.request.user)

    def perform_create(self, serializer):
        # Взаимодействие автоматически привязывается к текущему пользователю
        serializer.save(from_user=self.request.user)


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для просмотра мэтчей ТЕКУЩЕГО пользователя.
    """
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только те мэтчи, в которых он участвует
        user = self.request.user
        return Match.objects.filter(models.Q(user1=user) | models.Q(user2=user))
