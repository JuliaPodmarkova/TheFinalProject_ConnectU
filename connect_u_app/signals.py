# /app/connect_u_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # --- НАШ МАЯЧОК ---
    # Мы добавим вывод в консоль, чтобы точно знать, какой код работает.
    print(f"--- СИГНАЛ СРАБОТАТЬ! Пользователь: {instance.email}, Флаг created: {created} ---")

    if created:
        print(f"--- Флаг created=True. СОЗДАЕМ ПРОФИЛЬ... ---")
        UserProfile.objects.get_or_create(user=instance)
    else:
        print(f"--- Флаг created=False. Профиль не создаем. ---")
