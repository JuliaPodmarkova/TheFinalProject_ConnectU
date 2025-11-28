# create_missing_profiles.py
import os
import django

# Настраиваем окружение Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connect_u.settings')
django.setup()

from connect_u_app.models import User, UserProfile


def run():
    """
    Находит всех пользователей без профиля и создает для них пустой профиль.
    """
    users_without_profile = User.objects.filter(profile__isnull=True)
    count = 0

    print(f"Найдено пользователей без профиля: {users_without_profile.count()}")

    for user in users_without_profile:
        try:
            # Пытаемся создать профиль с какими-то значениями по умолчанию
            UserProfile.objects.create(
                user=user,
                full_name=user.email.split('@')[0],  # Используем часть email как временное имя
                city="Город не указан"
            )
            print(f"✅ Создан профиль для пользователя: {user.email}")
            count += 1
        except Exception as e:
            print(f"❌ Не удалось создать профиль для {user.email}: {e}")

    print(f"\nГотово! Успешно создано профилей: {count}.")


if __name__ == '__main__':
    run()