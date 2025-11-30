from datetime import date
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.files import File
from django.db.models import Q, UniqueConstraint
from PIL import Image
from io import BytesIO
import os


# =========================================================
# 👇 НАЧАЛО НОВОГО КОДА (ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ) 👇
# =========================================================

def user_photos_path(instance, filename):
    # Файлы будут загружаться в MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.user.id}/{filename}'


# =========================================================
# 👆 КОНЕЦ НОВОГО КОДА 👆
# =========================================================

class CustomUserManager(BaseUserManager):

    def create_user(self, email, password, **extra_fields):

        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        username = email
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    GENDER_CHOICES = (
        ('M', 'Мужчина'),
        ('F', 'Женщина'),
    )
    email = models.EmailField(_('email address'), unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F')
    birth_date = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                        (today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None


class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название интереса")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Интерес"
        verbose_name_plural = "Интересы"
        ordering = ['name']


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('searching', 'В поиске'), ('in_relationship', 'В отношениях'), ('not_specified', 'Не указано')],
        default='not_specified'
    )
    interests = models.ManyToManyField(Interest, blank=True, verbose_name="Интересы")
    bio = models.TextField(blank=True, null=True, verbose_name="О себе")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/default.png')

    def __str__(self):
        return self.user.email

    @property
    def age(self):
        if self.user.birth_date:
            today = date.today()
            return today.year - self.user.birth_date.year - (
                    (today.month, today.day) < (self.user.birth_date.month, self.user.birth_date.day))
        return None


class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    # 👇 ИЗМЕНЕНИЕ 1: Улучшаем путь для загрузки фото 👇
    image = models.ImageField(upload_to=user_photos_path)
    is_main = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # =========================================================
    # 👇 НАЧАЛО НОВОГО КОДА (ЛОГИКА СЖАТИЯ ФОТО) 👇
    # =========================================================
    def save(self, *args, **kwargs):
        if self.image:
            pil_img = Image.open(self.image)
            max_width, max_height = 800, 800

            if pil_img.width > max_width or pil_img.height > max_height:
                pil_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                in_mem_file = BytesIO()
                img_format = pil_img.format if pil_img.format in ['JPEG', 'PNG'] else 'JPEG'
                pil_img.save(in_mem_file, format=img_format)
                in_mem_file.seek(0)

                self.image = File(in_mem_file, name=self.image.name)

        super().save(*args, **kwargs)
    # =========================================================
    # 👆 КОНЕЦ НОВОГО КОДА 👆
    # =========================================================


class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} likes {self.to_user}"


class Dislike(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dislikes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dislikes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} dislikes {self.to_user}"


class Interaction(models.Model):
    REACTION_CHOICES = [('like', 'Like'), ('dislike', 'Dislike')]
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions_from')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions_to')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, full_name=f"{instance.first_name} {instance.last_name}".strip())
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            UserProfile.objects.create(user=instance)


class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user2')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    class Meta:
        verbose_name = "Мэтч"
        verbose_name_plural = "Мэтчи"
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Мэтч между {self.user1.username} и {self.user2.username}"

    def save(self, *args, **kwargs):
        # Гарантируем, что user1.id всегда меньше user2.id для простоты поиска
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super(Match, self).save(*args, **kwargs)


class ChatMessage(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages', verbose_name="Мэтч")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Отправитель")
    content = models.TextField(verbose_name="Содержание")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['timestamp']

    def __str__(self):
        return f"Сообщение от {self.sender.username} в {self.timestamp.strftime('%Y-%m-%d %H:%M')}"