from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q, F, CheckConstraint
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.files import File
from PIL import Image
from io import BytesIO


# --- МЕНЕДЖЕР ДЛЯ ПРОДВИНУТОЙ МОДЕЛИ USER ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('Поле Email должно быть заполнено'))
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
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


# --- ПРОДВИНУТАЯ МОДЕЛЬ USER ---
class User(AbstractUser):
    GENDER_CHOICES = (('M', 'Мужчина'), ('F', 'Женщина'))
    email = models.EmailField(_('email address'), unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
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

    @property
    def likes_received_count(self):
        return self.likes_received.count()


# --- МОДЕЛЬ ИНТЕРЕСОВ ---
class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self): return self.name

    class Meta: ordering = ['name']


# --- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---
class UserProfile(models.Model):
    STATUS_CHOICES = [('searching', 'В поиске'), ('in_relationship', 'В отношениях'), ('not_specified', 'Не указано')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', verbose_name="Аватар")
    interests = models.ManyToManyField(Interest, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_specified',
                              verbose_name="Статус отношений")
    show_age = models.BooleanField(default=True, verbose_name="Показывать возраст в профиле")
    show_city = models.BooleanField(default=True, verbose_name="Показывать город в профиле")
    searchable = models.BooleanField(default=True, verbose_name="Разрешить находить мой профиль в поиске")

    def __str__(self): return self.full_name or self.user.email

    @property
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'): return self.avatar.url
        return settings.STATIC_URL + 'images/default_avatar.png'


# --- ФОТОГРАФИИ В ГАЛЕРЕЕ ---
def user_photos_path(instance, filename): return f'user_{instance.user.id}/{filename}'


class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to=user_photos_path)
    is_main = models.BooleanField(default=False, verbose_name="Главное фото")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:
            pil_img = Image.open(self.image)
            max_width, max_height = 1024, 1024
            if pil_img.width > max_width or pil_img.height > max_height:
                pil_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                in_mem_file = BytesIO()
                if pil_img.mode in ("RGBA", "P"): pil_img = pil_img.convert("RGB")
                pil_img.save(in_mem_file, format='JPEG', quality=90)
                in_mem_file.seek(0)
                original_name, _ = self.image.name.rsplit('.', 1)
                new_name = f"{original_name}.jpg"
                self.image = File(in_mem_file, name=new_name)
        super().save(*args, **kwargs)


# --- ЛАЙКИ И ДИЗЛАЙКИ ---
class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: unique_together = ('from_user', 'to_user')


class Dislike(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dislikes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dislikes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: unique_together = ('from_user', 'to_user')


# --- МЭТЧИ И СООБЩЕНИЯ ---
class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_match'),
            CheckConstraint(check=~Q(user1=F('user2')), name='users_cannot_be_the_same'),
        ]

    def __str__(self): return f"Match between {self.user1.email} and {self.user2.email}"


class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ['timestamp']


# --- ВЗАИМОДЕЙСТВИЯ (ВОЗВРАЩЕНА) ---
class Interaction(models.Model):
    REACTION_CHOICES = (('like', 'Like'), ('dislike', 'Dislike'))
    from_user = models.ForeignKey(User, related_name='interactions_from', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='interactions_to', on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: unique_together = ('from_user', 'to_user')

    def __str__(self): return f'{self.from_user.username} -> {self.to_user.username}: {self.reaction}'


# --- СИГНАЛЫ ---

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created: UserProfile.objects.create(user=instance, full_name=instance.username.split('@')[0])
    if hasattr(instance, 'profile'): instance.profile.save()


@receiver(post_save, sender=Photo)
def ensure_single_main_photo(sender, instance, created, **kwargs):
    if instance.is_main:
        Photo.objects.filter(user=instance.user).exclude(pk=instance.pk).update(is_main=False)
        profile = instance.user.profile
        if profile.avatar != instance.image:
            profile.avatar = instance.image
            profile.save()


# НОВОЕ: Сигналы для синхронизации Like/Dislike с Interaction
@receiver(post_save, sender=Like)
def sync_like_to_interaction(sender, instance, created, **kwargs):
    Interaction.objects.update_or_create(
        from_user=instance.from_user,
        to_user=instance.to_user,
        defaults={'reaction': 'like', 'created_at': instance.created_at}
    )


@receiver(post_save, sender=Dislike)
def sync_dislike_to_interaction(sender, instance, created, **kwargs):
    Interaction.objects.update_or_create(
        from_user=instance.from_user,
        to_user=instance.to_user,
        defaults={'reaction': 'dislike', 'created_at': instance.created_at}
    )


@receiver(post_delete, sender=Like)
@receiver(post_delete, sender=Dislike)
def delete_interaction(sender, instance, **kwargs):
    Interaction.objects.filter(from_user=instance.from_user, to_user=instance.to_user).delete()
