from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Photo, Interest, Interaction, Match, ChatMessage

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'date_joined')
    search_fields = ('email', 'username')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'status')
    search_fields = ('user__email', 'full_name', 'city')

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_main', 'uploaded_at')
    list_filter = ('user', 'is_main')

class InterestAdmin(admin.ModelAdmin):
    search_fields = ('name',)

class InteractionAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'reaction')
    list_filter = ('reaction',)
    search_fields = ('from_user__email', 'to_user__email')

class MatchAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'timestamp')
    search_fields = ('user1__email', 'user2__email')

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('match', 'sender', 'timestamp')
    list_filter = ('match',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(Interest, InterestAdmin)
admin.site.register(Interaction, InteractionAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)