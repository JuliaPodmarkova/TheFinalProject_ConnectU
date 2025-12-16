from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Like, Dislike, Match, Photo, Interest, Message, ProfileView, Invitation


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль пользователя'
    fields = ('full_name', 'bio', 'city', 'searchable', 'search_gender', 'search_min_age', 'search_max_age',
              'show_city')


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'gender', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')  # Ищем по email вместо username
    ordering = ['email']  # Сортируем по email

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'gender', 'birth_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )


# Перерегистрация стандартной модели User
if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'searchable')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'city')  # Ищем по email пользователя


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'is_main', 'uploaded_at')
    list_filter = ('is_main', 'user')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at')
    search_fields = ('from_user__email', 'to_user__email')


@admin.register(Dislike)
class DislikeAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at')
    search_fields = ('from_user__email', 'to_user__email')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at')
    search_fields = ('user1__email', 'user2__email')


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('match', 'sender', 'timestamp')
    list_filter = ('match',)
    search_fields = ('sender__email', 'content')


@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'timestamp')
    search_fields = ('from_user__email', 'to_user__email')


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'match', 'created_at')
    list_filter = ('status',)
    search_fields = ('from_user__email', 'to_user__email')