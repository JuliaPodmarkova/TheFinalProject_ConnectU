from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import F, Q

from ..models import User, Like, Dislike, Match  # <- Добавили Match


@login_required
def like_user_view(request, user_id):
    if request.method == 'POST':
        current_user = request.user
        liked_user = get_object_or_404(User, id=user_id)

        # Создаем лайк
        Like.objects.get_or_create(from_user=current_user, to_user=liked_user)

        # 👇👇👇 НАЧАЛО НОВОЙ ЛОГИКИ МЭТЧА 👇👇👇
        # Проверяем, есть ли ответный лайк
        if Like.objects.filter(from_user=liked_user, to_user=current_user).exists():
            # Чтобы избежать дубликатов (A,B) и (B,A), упорядочиваем ID
            user_a, user_b = sorted([current_user, liked_user], key=lambda u: u.id)

            # Создаем мэтч, если его еще нет
            match, created = Match.objects.get_or_create(user1=user_a, user2=user_b)

            if created:
                messages.success(request, f"🎉 Это мэтч с {liked_user.profile.full_name}! Теперь вы можете общаться.")
        # 👆👆👆 КОНЕЦ НОВОЙ ЛОГИКИ МЭТЧА 👆👆👆

    return redirect(reverse('home'))


@login_required
def dislike_user_view(request, user_id):
    if request.method == 'POST':
        current_user = request.user
        disliked_user = get_object_or_404(User, id=user_id)
        Dislike.objects.get_or_create(from_user=current_user, to_user=disliked_user)
    return redirect(reverse('home'))