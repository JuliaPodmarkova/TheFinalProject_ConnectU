from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile
import logging
from allauth.account.signals import user_signed_up

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    print(f"--- СИГНАЛ СРАБОТАТЬ! Пользователь: {instance.email}, Флаг created: {created} ---")

    if created:
        print(f"--- Флаг created=True. СОЗДАЕМ ПРОФИЛЬ... ---")
        UserProfile.objects.get_or_create(user=instance)
    else:
        print(f"--- Флаг created=False. Профиль не создаем. ---")

@receiver(user_signed_up)
def create_user_profile_on_social_signup(request, user, sociallogin, **kwargs):

    if not hasattr(user, 'profile'):
        extra_data = sociallogin.account.extra_data
        first_name = extra_data.get('given_name', '')
        last_name = extra_data.get('family_name', '')
        full_name = f"{first_name} {last_name}".strip()

        UserProfile.objects.create(user=user, full_name=full_name)
        logger.info(f"✅ ПРОФИЛЬ: Автоматически создан и заполнен профиль для {user.email} с именем '{full_name}'")

