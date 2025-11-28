from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from ..models import Like, Dislike, Interaction, User


@login_required
@require_POST  # Эта view принимает только POST запросы
def process_reaction_view(request, user_id, reaction):
    """
    Общая логика для обработки реакции (лайк/дизлайк) и подбора следующего пользователя.
    """
    # 1. Найти пользователя, на которого отреагировали
    target_user = get_object_or_404(User, id=user_id)

    # 2. Создать запись о взаимодействии (или обновить, если она уже есть)
    Interaction.objects.update_or_create(
        from_user=request.user,
        to_user=target_user,
        defaults={'reaction': reaction}
    )

    # 3. Найти ID всех, с кем уже было взаимодействие (включая нового)
    interacted_user_ids = Interaction.objects.filter(
        from_user=request.user
    ).values_list('to_user_id', flat=True)

    # 4. Найти СЛЕДУЮЩЕГО пользователя для показа (та же логика, что и в home_view)
    recommended_user = User.objects.select_related('profile').exclude(
        id=request.user.id
    ).exclude(
        id__in=interacted_user_ids
    ).exclude(
        gender=request.user.gender
    ).first()

    context = {'recommended_user': recommended_user}

    # 5. Вернуть только HTML-фрагмент карточки, который HTMX вставит в страницу
    return render(request, 'user_card.html', context)


def get_next_recommendation(user):
    """
    Вспомогательная функция для поиска следующей анкеты.
    Она исключает самого себя, тех, кого уже лайкнул/дизлайкнул.
    """
    # ID пользователей, с которыми уже было взаимодействие
    liked_user_ids = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    disliked_user_ids = Dislike.objects.filter(from_user=user).values_list('to_user_id', flat=True)

    # Объединяем все ID, которые нужно исключить
    excluded_user_ids = set(liked_user_ids) | set(disliked_user_ids)
    excluded_user_ids.add(user.id)  # Добавляем ID самого пользователя

    # Ищем всех пользователей, КРОМЕ тех, что в списке исключений
    recommended_users = User.objects.exclude(id__in=excluded_user_ids)

    # Для отладки: выводим, сколько кандидатов найдено
    print(f"Пользователь {user.email} | Найдено кандидатов для показа: {recommended_users.count()}")

    # Берем первого случайного из оставшихся
    return recommended_users.order_by('?').first()

@login_required
@require_POST # Эта view будет принимать только POST запросы
def like_user_view(request, pk):
    """
    Обрабатывает лайк, сохраняет его и возвращает HTML-фрагмент
    со следующей анкетой для HTMX.
    """
    from_user = request.user
    to_user = get_object_or_404(User, pk=pk)

    # Создаем лайк (или обновляем, если пользователь передумал)
    Like.objects.update_or_create(from_user=from_user, to_user=to_user)
    # Удаляем дизлайк, если он был
    Dislike.objects.filter(from_user=from_user, to_user=to_user).delete()

    # !!! Тут можно будет добавить логику проверки на мэтч (позже)

    # Находим следующего пользователя для показа
    next_user = get_next_recommendation(request.user)

    # Возвращаем HTML-фрагмент с новой анкетой
    return render(request, 'partials/user_card.html', {'recommended_user': next_user})


@login_required
@require_POST # Эта view будет принимать только POST запросы
def dislike_user_view(request, pk):
    """
    Обрабатывает дизлайк и возвращает HTML-фрагмент для HTMX.
    """
    from_user = request.user
    to_user = get_object_or_404(User, pk=pk)

    # Создаем дизлайк
    Dislike.objects.update_or_create(from_user=from_user, to_user=to_user)
    # Удаляем лайк, если он был
    Like.objects.filter(from_user=from_user, to_user=to_user).delete()

    # Находим следующего пользователя для показа
    next_user = get_next_recommendation(request.user)

    # Возвращаем HTML-фрагмент с новой анкетой
    return render(request, 'partials/user_card.html', {'recommended_user': next_user})