from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import CheckConstraint, F, Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image
from io import BytesIO
from django.core.files import File

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Поле Email должно быть заполнено'))
        email = self.normalize_email(email)
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

class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = (('M', 'Мужчина'), ('F', 'Женщина'))
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Пол', null=True, blank=True)
    birth_date = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
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

class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Интерес"
        verbose_name_plural = "Интересы"

class UserProfile(models.Model):
    STATUS_CHOICES = [
        ('searching', 'В поиске'),
        ('in_relationship', 'В отношениях'),
        ('not_specified', 'Не указано')
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True, verbose_name="Полное имя")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    bio = models.TextField(blank=True, verbose_name="О себе")
    interests = models.ManyToManyField(Interest, blank=True, verbose_name="Интересы")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_specified',
                              verbose_name="Статус отношений")
    search_gender = models.CharField(max_length=1, choices=User.GENDER_CHOICES, blank=True, null=True,
                                     verbose_name="Искать пол")
    search_min_age = models.PositiveSmallIntegerField(null=True, blank=True, default=18,
                                                      verbose_name="Минимальный возраст для поиска")
    search_max_age = models.PositiveSmallIntegerField(null=True, blank=True, default=99,
                                                      verbose_name="Максимальный возраст для поиска")
    show_age = models.BooleanField(default=True, verbose_name="Показывать возраст в профиле")
    show_city = models.BooleanField(default=True, verbose_name="Показывать город в профиле")
    searchable = models.BooleanField(default=True, verbose_name="Разрешить находить мой профиль в поиске")

    def __str__(self):
        return self.full_name or self.user.email

    def get_avatar_url(self):
        main_photo = self.user.photos.filter(is_main=True).first()
        if main_photo and main_photo.image and hasattr(main_photo.image, 'url'):
            return main_photo.image.url
        first_photo = self.user.photos.first()
        if first_photo and first_photo.image and hasattr(first_photo.image, 'url'):
            return first_photo.image.url
        return settings.STATIC_URL + 'images/default_avatar.png'

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

def user_photos_path(instance, filename):
    return f'user_{instance.user.id}/{filename}'

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos', verbose_name="Пользователь")
    image = models.ImageField(upload_to=user_photos_path, verbose_name="Изображение")
    is_main = models.BooleanField(default=False, verbose_name="Главное фото")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            pil_img = Image.open(self.image)
            max_width, max_height = 1024, 1024
            if pil_img.width > max_width or pil_img.height > max_height:
                pil_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                in_mem_file = BytesIO()
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")
                pil_img.save(in_mem_file, format='JPEG', quality=90)
                in_mem_file.seek(0)
                original_name, _ = self.image.name.rsplit('.', 1)
                new_name = f"{original_name}.jpg"
                self.image = File(in_mem_file, name=new_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Фото для {self.user.email}"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"

class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"

class Dislike(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dislikes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dislikes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
        verbose_name = "Дизлайк"
        verbose_name_plural = "Дизлайки"

class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_match'),
            CheckConstraint(check=~Q(user1=F('user2')), name='users_cannot_be_the_same'),
        ]
        verbose_name = "Мэтч"
        verbose_name_plural = "Мэтчи"

    def __str__(self): return f"Match between {self.user1.email} and {self.user2.email}"

class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False) # <-- ВОТ НОВОЕ ПОЛЕ

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def get_formatted_timestamp(self):
        local_time = timezone.localtime(self.timestamp)
        return local_time.strftime('%H:%M')

class Interaction(models.Model):
    REACTION_CHOICES = (('like', 'Like'), ('dislike', 'Dislike'))
    from_user = models.ForeignKey(User, related_name='interactions_from', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='interactions_to', on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = "Взаимодействие"
        verbose_name_plural = "Взаимодействия"

    def __str__(self): return f'{self.from_user.email} -> {self.to_user.email}: {self.reaction}'

class ProfileView(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_profiles')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_viewers')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-timestamp']
        verbose_name = "Просмотр профиля"
        verbose_name_plural = "Просмотры профилей"

    def __str__(self):
        return f'{self.from_user.email} viewed {self.to_user.email}'

class Invitation(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Отправлено'),
        ('accepted', 'Принято'),
        ('declined', 'Отклонено'),
    ]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='invitations')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    message = models.TextField(blank=True, verbose_name="Сообщение-приглашение")
    contact_info = models.CharField(max_length=255, blank=True, verbose_name="Контактная информация")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Приглашение"
        verbose_name_plural = "Приглашения"
        constraints = [
            models.UniqueConstraint(fields=['match', 'from_user'], condition=Q(status='sent'), name='unique_active_invitation_per_match')
        ]

    def __str__(self):
        return f'Invitation from {self.from_user.email} to {self.to_user.email} in match {self.match.id}'

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Photo)
def ensure_single_main_photo(sender, instance, **kwargs):
    if instance.is_main:
        Photo.objects.filter(user=instance.user).exclude(pk=instance.pk).update(is_main=False)

@receiver(post_save, sender=Like)
def sync_like_to_interaction(sender, instance, created, **kwargs):
    Interaction.objects.update_or_create(
        from_user=instance.from_user, to_user=instance.to_user,
        defaults={'reaction': 'like', 'created_at': instance.created_at}
    )

@receiver(post_save, sender=Dislike)
def sync_dislike_to_interaction(sender, instance, created, **kwargs):
    Interaction.objects.update_or_create(
        from_user=instance.from_user, to_user=instance.to_user,
        defaults={'reaction': 'dislike', 'created_at': instance.created_at}
    )

@receiver(post_delete, sender=Like)
@receiver(post_delete, sender=Dislike)
def delete_interaction(sender, instance, **kwargs):
    Interaction.objects.filter(from_user=instance.from_user, to_user=instance.to_user).delete()