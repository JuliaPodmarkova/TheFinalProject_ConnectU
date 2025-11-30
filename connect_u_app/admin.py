from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Photo, Interest, Like, Dislike, Match, Message

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'date_joined')
    search_fields = ('email', 'username')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city')
    search_fields = ('user__username', 'full_name', 'city')

class PhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'uploaded_at')
    list_filter = ('user',)

class InterestAdmin(admin.ModelAdmin):
    search_fields = ('name',)

class MatchAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at')
    search_fields = ('user1__username', 'user2__username')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('match', 'sender', 'timestamp')
    list_filter = ('match',)
    search_fields = ('sender__username', 'content')


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(Interest, InterestAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Like)
admin.site.register(Dislike)
