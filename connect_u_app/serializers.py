from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import UserProfile, Interest, Photo, Match, Interaction


User = get_user_model()


class UserSerializerForProfile(serializers.ModelSerializer):
    """
    Упрощенный сериализатор пользователя для вложения в профиль.
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'gender', 'age']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели UserProfile.
    """
    user = UserSerializerForProfile(read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)

    interests = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user',
            'full_name',
            'bio',
            'city',
            'status',
            'interests',
            'avatar_url',
        ]

# Этот сериализатор будет использоваться в UserViewSet из api.py
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'gender', 'age']

# Этот сериализатор ты использовала в ProfileSerializer, но мы его переименуем для ясности
# и чтобы api.py мог его найти
UserProfileSerializer = ProfileSerializer

# Сериализатор для модели Photo
class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'user', 'image', 'is_main', 'uploaded_at']
        read_only_fields = ['user']

# Сериализатор для модели Interaction (если она у тебя используется)
class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__' # Включаем все поля
        read_only_fields = ['from_user']

# Сериализатор для модели Match
class MatchSerializer(serializers.ModelSerializer):
    # Показываем базовую информацию о пользователях в мэтче
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'user1', 'user2', 'created_at']