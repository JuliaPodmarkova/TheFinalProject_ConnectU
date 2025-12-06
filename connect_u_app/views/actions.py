from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import F, Q
from django.http import HttpResponse

from ..models import User, Like, Dislike, Match, Photo


@login_required
def like_user_view(request, user_id):
    if request.method == 'POST':
        current_user = request.user
        liked_user = get_object_or_404(User, id=user_id)

        Like.objects.get_or_create(from_user=current_user, to_user=liked_user)

        if Like.objects.filter(from_user=liked_user, to_user=current_user).exists():
            user_a, user_b = sorted([current_user, liked_user], key=lambda u: u.id)
            match, created = Match.objects.get_or_create(user1=user_a, user2=user_b)

            if created and request.htmx:
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
                response = HttpResponse(html)
                response['HX-Trigger'] = 'showMatchModal'
                return response

        if request.htmx:
            return HttpResponse(status=200)

    return redirect(reverse('home'))


@login_required
def dislike_user_view(request, user_id):
    if request.method == 'POST':
        current_user = request.user
        disliked_user = get_object_or_404(User, id=user_id)
        Dislike.objects.get_or_create(from_user=current_user, to_user=disliked_user)

        if request.htmx:
            return HttpResponse(status=200)

    return redirect(reverse('home'))

@login_required
def delete_photo_view(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id, user=request.user)
    if request.method == 'POST':
        is_main = photo.is_main
        photo.delete()
        messages.success(request, 'Фотография удалена.')
        if is_main:
            new_main = request.user.photos.first()
            if new_main:
                new_main.is_main = True
                new_main.save()
    return redirect('profile_photos')

@login_required
def set_main_photo_view(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id, user=request.user)
    if request.method == 'POST':
        request.user.photos.update(is_main=False)
        photo.is_main = True
        photo.save()
        messages.success(request, 'Главное фото обновлено.')
    return redirect('profile_photos')