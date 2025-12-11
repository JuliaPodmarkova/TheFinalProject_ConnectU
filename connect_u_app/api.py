from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    User,
    UserProfile,
    Photo,
    Interaction,
    Match,
    Like,
    Dislike
)

from .serializers import (
    UserProfileSerializer,
    UserSerializer,
    PhotoSerializer,
    InteractionSerializer,
    MatchSerializer,
)


class UserProfileViewSet(viewsets.ModelViewSet):

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = User.objects.all().exclude(is_staff=True, is_superuser=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().exclude(pk=self.request.user.pk)

    @action(detail=True, methods=['post'], url_path='like')
    def like_user(self, request, pk=None):

        current_user = request.user
        liked_user = get_object_or_404(User, pk=pk)

        if current_user == liked_user:
            return Response({'error': 'You cannot like yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        Like.objects.get_or_create(from_user=current_user, to_user=liked_user)

        is_match = Like.objects.filter(from_user=liked_user, to_user=current_user).exists()

        if is_match:
            user_a, user_b = sorted([current_user, liked_user], key=lambda u: u.id)
            Match.objects.get_or_create(user1=user_a, user2=user_b)

        return Response({'status': 'like set', 'match': is_match}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='dislike')
    def dislike_user(self, request, pk=None):

        current_user = request.user
        disliked_user = get_object_or_404(User, pk=pk)

        if current_user == disliked_user:
            return Response({'error': 'You cannot dislike yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        Dislike.objects.get_or_create(from_user=current_user, to_user=disliked_user)

        return Response({'status': 'dislike set'}, status=status.HTTP_200_OK)


class PhotoViewSet(viewsets.ModelViewSet):

    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Photo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InteractionViewSet(viewsets.ModelViewSet):

    serializer_class = InteractionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Interaction.objects.filter(from_user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

class MatchViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(models.Q(user1=user) | models.Q(user2=user))
