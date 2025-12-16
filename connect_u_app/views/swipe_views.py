from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from ..models import User, Like, Dislike, Match
from django.views.decorators.http import require_POST
import json
from datetime import date, timedelta

def get_next_user_for_swipe(current_user):
    """Возвращает следующего пользователя для свайпа."""
    liked_ids = Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True)
    disliked_ids = Dislike.objects.filter(from_user=current_user).values_list('to_user_id', flat=True)
    excluded_ids = set(liked_ids) | set(disliked_ids)
    excluded_ids.add(current_user.id)
    profile = current_user.profile
    users = User.objects.exclude(id__in=excluded_ids)
    if profile.search_gender:
        users = users.filter(gender=profile.search_gender)
    if profile.search_min_age:
        latest_birth_date = date.today() - timedelta(days=int(profile.search_min_age * 365.25))
        users = users.filter(birth_date__lte=latest_birth_date)
    if profile.search_max_age:
        earliest_birth_date = date.today() - timedelta(days=int((profile.search_max_age + 1) * 365.25))
        users = users.filter(birth_date__gte=earliest_birth_date)
    return users.order_by('?').first()

@login_required
def swipe_main_view(request):
    """Отображает основную страницу для свайпов (контейнер)."""
    return render(request, 'swipe/main.html')

@login_required
def get_next_profile(request):
    """HTMX-эндпоинт для получения карточки следующего пользователя."""
    next_user = get_next_user_for_swipe(request.user)
    if next_user:
        return render(request, 'swipe/card.html', {'profile_user': next_user})
    else:
        return HttpResponse(
            "<div class='text-center h4 m-5'>Больше никого нет... Попробуйте изменить фильтры в профиле!</div>")

@login_required
@require_POST
def swipe(request):
    """Обрабатывает лайк или дизлайк и возвращает следующую карточку."""
    # ИСПРАВЛЕНИЕ: HTMX с hx-vals отправляет данные в request.POST, а не в request.body
    user_id = request.POST.get('user_id')
    action = request.POST.get('action')

    if not user_id or not action:
        return HttpResponse("Missing data", status=400)

    to_user = User.objects.get(id=user_id)
    from_user = request.user
    if action == 'like':
        Like.objects.get_or_create(from_user=from_user, to_user=to_user)
        is_match = Like.objects.filter(from_user=to_user, to_user=from_user).exists()
        next_user = get_next_user_for_swipe(from_user)
        response = render(request, 'swipe/card.html', {'profile_user': next_user})
        if is_match:
            Match.objects.get_or_create(
                user1=min(from_user, to_user, key=lambda u: u.id),
                user2=max(from_user, to_user, key=lambda u: u.id)
            )
            match_data = {
                "matchName": to_user.profile.full_name,
                "matchAvatarUrl": to_user.profile.get_avatar_url()
            }
            response['HX-Trigger'] = json.dumps({'matchOccurred': match_data})
        return response
    elif action == 'dislike':
        Dislike.objects.get_or_create(from_user=from_user, to_user=to_user)
        next_user = get_next_user_for_swipe(from_user)
        return render(request, 'swipe/card.html', {'profile_user': next_user})
    return HttpResponse(status=400)