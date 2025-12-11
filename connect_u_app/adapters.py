import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def __init__(self, request: HttpRequest | None = None):
        logger.debug("🕵️‍♂️ ADAPTER: __init__ - Адаптер был создан!")
        super().__init__(request)

    def pre_social_login(self, request, sociallogin):

        logger.debug(f"🕵️‍♂️ ADAPTER: pre_social_login - Входные данные:")
        logger.debug(f"  - Пользователь уже существует? {'Да' if sociallogin.is_existing else 'Нет'}")
        logger.debug(f"  - Email от провайдера: {sociallogin.account.extra_data.get('email')}")
        logger.debug(f"  - UID от провайдера: {sociallogin.account.uid}")

        super().pre_social_login(request, sociallogin)

    def is_open_for_signup(self, request, sociallogin):

        email = sociallogin.account.extra_data.get('email', '').lower()
        logger.debug(f"🕵️‍♂️ ADAPTER: is_open_for_signup - Проверяем, можно ли создать аккаунт для {email}?")

        allow_signup = True
        logger.debug(f"  - РЕШЕНИЕ: Регистрация {'разрешена' if allow_signup else 'ЗАПРЕЩЕНА'}.")
        return allow_signup