# connect_u_app/views/interactions.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from ..models import Like, Dislike, Match, User
import json

def get_next_recommendation(user):
    liked_user_ids = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    disliked_user_ids = Dislike.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    excluded_user_ids = set(liked_user_ids) | set(disliked_user_ids)
    excluded_user_ids.add(user.id)

    recommended_users = User.objects.exclude(id__in=excluded_user_ids).select_related('profile')
    return recommended_users.order_by('?').first()

@login_required
def swipe_view(request):
    return render(request, 'main.html')

@login_required
def show_next_user_view(request):
    next_user = get_next_recommendation(request.user)
    return render(request, 'partials/user_card.html', {'user_obj': next_user})

@login_required
@require_POST
# 👇 ИСПРАВЛЕНИЕ TypeError: меняем 'pk' на 'user_id' 👇
def like_user_view(request, user_id):
    from_user = request.user
    to_user = get_object_or_404(User, id=user_id)

    Like.objects.update_or_create(from_user=from_user, to_user=to_user)
    Dislike.objects.filter(from_user=from_user, to_user=to_user).delete()

    reciprocal_like = Like.objects.filter(from_user=to_user, to_user=from_user).exists()

    next_user = get_next_recommendation(from_user)
    response = render(request, 'partials/user_card.html', {'user_obj': next_user})

    if reciprocal_like:
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

@login_required
@require_POST
# 👇 И для единообразия меняем здесь тоже 👇
def dislike_user_view(request, user_id):
    from_user = request.user
    to_user = get_object_or_404(User, id=user_id)
    Dislike.objects.update_or_create(from_user=from_user, to_user=to_user)
    Like.objects.filter(from_user=from_user, to_user=to_user).delete()

    next_user = get_next_recommendation(from_user)
    return render(request, 'partials/user_card.html', {'user_obj': next_user})