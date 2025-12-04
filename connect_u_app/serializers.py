from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import UserProfile, Interest  # <--- ИЗМЕНЕНИЕ: импортируем UserProfile

User = get_user_model()


class UserSerializerForProfile(serializers.ModelSerializer):
    """
    Упрощенный сериализатор пользователя для вложения в профиль.
    """

    class Meta:
        model = User
        # Добавим age из свойства модели User
        fields = ['id', 'username', 'email', 'gender', 'age']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели UserProfile.
    """
    user = UserSerializerForProfile(read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)

    # ИЗМЕНЕНИЕ: Правильно обрабатываем ManyToMany поле 'interests'
    # StringRelatedField будет использовать __str__ метод модели Interest (т.е. вернет названия интересов)
    interests = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = UserProfile  # <--- ИЗМЕНЕНИЕ: указали правильную модель
        fields = [
            'user',
            'full_name',
            'bio',
            'city',
            'status',
            'interests',  # <--- ИЗМЕНЕНИЕ: используем реальное имя поля
            'avatar_url',
        ]