# connect_u_app/views/pages.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from ..models import UserProfile, Interest, User, Like, Dislike
from ..forms import UserEditForm, UserProfileEditForm


# ==============================================================================
# ОСНОВНЫЕ СТРАНИЦЫ И ЛЕНТА
# ==============================================================================

@login_required
def index(request):
    """
    Главная страница (Лента). Находит и показывает первую рекомендованную анкету.
    """
    current_user = request.user

    # Пользователи, с которыми уже было взаимодействие (лайк или дизлайк)
    interacted_users_ids = list(Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))
    interacted_users_ids += list(Dislike.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))

    # Исключаем себя и тех, с кем уже взаимодействовали
    recommended_user = User.objects.exclude(
        Q(id=current_user.id) | Q(id__in=interacted_users_ids)
    ).order_by('?').first()  # '?' - случайный порядок, first() - берем первого

    context = {
        'recommended_user': recommended_user
    }
    return render(request, 'home.html', context)


# ==============================================================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ==============================================================================

@login_required
def profile_own_view(request):
    """
    Страница для просмотра своего собственного профиля.
    """
    # Используем get_object_or_404 для надежности
    profile = get_object_or_404(UserProfile, user=request.user)
    context = {
        'profile': profile
    }
    return render(request, 'account/profile_own.html', context)


@login_required
def profile_edit_view(request):
    """
    Страница для редактирования профиля (УЛУЧШЕННАЯ ВЕРСИЯ).
    """
    user = request.user
    profile = get_object_or_404(UserProfile, user=user)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = UserProfileEditForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            # Сохраняем основные данные профиля, но пока без M2M
            saved_profile = profile_form.save(commit=False)
            saved_profile.save()

            # --- НОВАЯ, НАДЕЖНАЯ ЛОГИКА СОХРАНЕНИЯ ИНТЕРЕСОВ ---

            # 1. Получаем интересы, выбранные в чекбоксах
            checkbox_interests = profile_form.cleaned_data.get('interests')

            # 2. Получаем и создаем интересы из текстового поля "Другие"
            custom_interests_list = []
            other_text = profile_form.cleaned_data.get('other_interests', '').strip()
            if other_text:
                interest_names = [name.strip().capitalize() for name in other_text.split(',') if name.strip()]
                for name in interest_names:
                    interest_obj, created = Interest.objects.get_or_create(name=name)
                    custom_interests_list.append(interest_obj)

            # 3. Объединяем оба списка и устанавливаем их для профиля
            # Метод .set() полностью заменяет старый набор интересов новым, объединенным.
            all_interests = list(checkbox_interests) + custom_interests_list
            saved_profile.interests.set(all_interests)

            # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

            # Добавляем сообщение об успехе для нашего будущего поп-ап окна
            messages.success(request, 'Ваши изменения успешно сохранены!')

            # Гарантированно перенаправляем на страницу профиля
            return redirect('profile_own')
        else:
            # Если форма невалидна, выводим сообщение об ошибке
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме. Они подсвечены красным.')

    else:  # GET-запрос
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileEditForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'account/profile_edit.html', context)