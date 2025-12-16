from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden
from ..models import User, Like, Dislike, Match, Photo, Invitation, Message
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


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


@login_required
def send_invitation(request, match_id):
    if request.method == 'POST':
        match = get_object_or_404(Match, id=match_id)
        if request.user != match.user1 and request.user != match.user2:
            return HttpResponseForbidden()
        to_user = match.user2 if request.user == match.user1 else match.user1
        if not Invitation.objects.filter(match=match, from_user=request.user, status='sent').exists():
            Invitation.objects.create(
                match=match,
                from_user=request.user,
                to_user=to_user,
                message=request.POST.get('message', ''),
                contact_info=request.POST.get('contact_info', '')
            )
            messages.success(request, 'Приглашение успешно отправлено!')
        else:
            messages.warning(request, 'Вы уже отправляли приглашение в этом чате. Дождитесь ответа.')
        return redirect('chat', match_id=match_id)
    return redirect('match_list')


@login_required
def handle_invitation(request, invitation_id):
    if request.method == 'POST':
        invitation = get_object_or_404(Invitation, id=invitation_id)
        if request.user != invitation.to_user:
            return HttpResponseForbidden()

        action = request.POST.get('action')
        system_message_content = ""

        if action == 'accept':
            invitation.status = 'accepted'
            messages.success(request, 'Вы приняли приглашение!')
            system_message_content = f"🤝 Приглашение принято! Контакты от {invitation.from_user.profile.full_name}: {invitation.contact_info}"

        elif action == 'decline':
            invitation.status = 'declined'
            messages.info(request, 'Вы отклонили приглашение.')
            system_message_content = f"🚫 Приглашение от {invitation.from_user.profile.full_name} было отклонено."

        invitation.save()

        if system_message_content:
            message = Message.objects.create(
                match=invitation.match,
                sender=request.user,
                content=system_message_content,
                is_system=True
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{invitation.match.id}',
                {
                    'type': 'chat_message',
                    'message': message.content,
                    'sender_id': message.sender.id,
                    'is_system': message.is_system,
                }
            )

        return redirect('chat', match_id=invitation.match.id)
    return redirect('match_list')