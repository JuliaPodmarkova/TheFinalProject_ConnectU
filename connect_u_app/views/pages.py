from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from ..models import UserProfile, Interest, User, Like, Dislike, Photo
from ..forms import UserEditForm, UserProfileEditForm, PhotoForm


@login_required
def index(request):
    current_user = request.user

    interacted_users_ids = list(Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))
    interacted_users_ids += list(Dislike.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))

    recommended_user = User.objects.exclude(
        Q(id=current_user.id) | Q(id__in=interacted_users_ids)
    ).order_by('?').first()

    context = {
        'recommended_user': recommended_user
    }
    return render(request, 'home.html', context)


@login_required
def profile_own_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    context = {
        'profile': profile
    }
    return render(request, 'account/profile_own.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = UserProfileEditForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()

            # =========================================================
            # 👇 НАЧАЛО НОВОЙ, СУПЕР-НАДЕЖНОЙ ЛОГИКИ СОХРАНЕНИЯ 👇
            # =========================================================

            # 1. Получаем набор интересов, выбранных в чекбоксах
            selected_interests = set(profile_form.cleaned_data.get('interests', []))

            # 2. Обрабатываем интересы, введенные вручную в текстовое поле
            other_text = profile_form.cleaned_data.get('other_interests', '').strip()
            if other_text:
                interest_names = [name.strip().capitalize() for name in other_text.split(',') if name.strip()]
                for name in interest_names:
                    # Находим или создаем объект Interest
                    interest_obj, created = Interest.objects.get_or_create(name=name)
                    # Добавляем его в наш общий набор
                    selected_interests.add(interest_obj)

            # 3. Сохраняем основные данные профиля, но ПОКА НЕ трогаем M2M связи
            saved_profile = profile_form.save(commit=False)
            saved_profile.save()

            # 4. Устанавливаем ПОЛНЫЙ И ОКОНЧАТЕЛЬНЫЙ список интересов ОДНИМ действием
            # Метод .set() очищает старые и записывает новые связи.
            saved_profile.interests.set(list(selected_interests))

            # =========================================================
            # 👆 КОНЕЦ НОВОЙ ЛОГИКИ 👆
            # =========================================================

            messages.success(request, 'Ваши изменения успешно сохранены!')
            return redirect('profile_own')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileEditForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'account/profile_edit.html', context)


@login_required
def photo_gallery_view(request):
    user_photos = Photo.objects.filter(user=request.user).order_by('-uploaded_at')

    if request.method == 'POST':
        photo_form = PhotoForm(request.POST, request.FILES)
        if photo_form.is_valid():
            photo = photo_form.save(commit=False)
            photo.user = request.user
            photo.save()
            messages.success(request, 'Фото успешно загружено!')
            return redirect('photo_gallery')
    else:
        photo_form = PhotoForm()

    context = {
        'photos': user_photos,
        'photo_form': photo_form
    }
    return render(request, 'account/photo_gallery.html', context)


@login_required
def match_list_view(request):
    # Находим все мэтчи, где участвует текущий пользователь
    matches = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1__profile', 'user2__profile').order_by('-created_at')

    context = {
        'matches': matches
    }
    return render(request, 'matches.html', context)


@login_required
def chat_view(request, match_id):
    # Находим мэтч или возвращаем 404
    match = get_object_or_404(Match, id=match_id)

    # Проверка безопасности: убеждаемся, что текущий юзер - участник этого мэтча
    if request.user != match.user1 and request.user != match.user2:
        return HttpResponseForbidden("У вас нет доступа к этому чату.")

    # Определяем, кто в чате "другой" пользователь
    other_user = match.user2 if request.user == match.user1 else match.user1

    # Обработка отправки нового сообщения
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                match=match,
                sender=request.user,
                content=content
            )
            return redirect('chat', match_id=match_id)

    # Получаем все сообщения для этого чата
    messages = match.messages.all().select_related('sender__profile')

    context = {
        'match': match,
        'other_user': other_user,
        'messages': messages
    }
    return render(request, 'chat.html', context)