from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import F, Q
from django.http import HttpResponse

from ..models import User, Like, Dislike, Match  # <- Добавили Match


@login_required
def like_user_view(request, user_id):
    if request.method == 'POST':
        current_user = request.user
        liked_user = get_object_or_404(User, id=user_id)

        # Создаем лайк
        Like.objects.get_or_create(from_user=current_user, to_user=liked_user)

        # Проверяем, случился ли мэтч
        if Like.objects.filter(from_user=liked_user, to_user=current_user).exists():
            user_a, user_b = sorted([current_user, liked_user], key=lambda u: u.id)
            match, created = Match.objects.get_or_create(user1=user_a, user2=user_b)

            # Если мэтч только что создан и это HTMX-запрос
            if created and request.htmx:
                # Создаем HTML-ответ с модальным окном
                html = f"""
                <div id="match-modal-content" hx-swap-oob="innerHTML">
                    <div class="modal-body text-center">
                        <img src="{liked_user.profile.get_avatar_url()}" class="rounded-circle mb-3" width="120" height="120" style="object-fit: cover;">
                        <h4>Это мэтч!</h4>
                        <p>Теперь вы с <strong>{liked_user.profile.full_name}</strong> можете общаться.</p>
                        <div class="d-grid gap-2">
                             <a href="/matches/" class="btn btn-primary">Перейти к диалогам</a>
                             <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Продолжить просмотр</button>
                        </div>
                    </div>
                </div>
                """
                # Отправляем событие, чтобы JS показал модальное окно
                response = HttpResponse(html)
                response['HX-Trigger'] = 'showMatchModal'
                return response

        # Если это обычный HTMX-запрос без мэтча, возвращаем пустой ответ, чтобы карточка исчезла
        if request.htmx:
            return HttpResponse(status=200)

    # Старая логика для обычных запросов
    return redirect(reverse('home'))


@login_required
def dislike_user_view(request, user_id):
    if request.method == 'POST':
        current_user = request.user
        disliked_user = get_object_or_404(User, id=user_id)
        Dislike.objects.get_or_create(from_user=current_user, to_user=disliked_user)

        # Если это HTMX-запрос, возвращаем пустой ответ
        if request.htmx:
            return HttpResponse(status=200)

    # Старая логика для обычных запросов
    return redirect(reverse('home'))
