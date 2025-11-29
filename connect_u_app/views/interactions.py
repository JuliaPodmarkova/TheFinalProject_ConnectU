from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q

from ..models import Like, Dislike, Match, User

def get_next_recommendation(user):

    liked_user_ids = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    disliked_user_ids = Dislike.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    excluded_user_ids = set(liked_user_ids) | set(disliked_user_ids)
    excluded_user_ids.add(user.id)
    recommended_users = User.objects.exclude(id__in=excluded_user_ids)
    return recommended_users.order_by('?').first()

@login_required
@require_POST
def like_user_view(request, pk):

    from_user = request.user
    to_user = get_object_or_404(User, pk=pk)
    is_match = False

    Like.objects.update_or_create(from_user=from_user, to_user=to_user)
    Dislike.objects.filter(from_user=from_user, to_user=to_user).delete()

    reciprocal_like = Like.objects.filter(from_user=to_user, to_user=from_user).exists()
    if reciprocal_like:
        is_match = True
        Match.objects.get_or_create(user1=min(from_user, to_user, key=lambda u: u.id),
                                   user2=max(from_user, to_user, key=lambda u: u.id))
        messages.success(request, f"Это мэтч! Теперь вы можете общаться с {to_user.profile.full_name}.")

    next_user = get_next_recommendation(from_user)

    if is_match:
        context = {
            'matched_user': to_user,
            'next_user': next_user,
        }
        return render(request, 'partials/match_modal.html', context)   # модальное окно мэтча
    else:
        return render(request, 'partials/user_card.html', {'recommended_user': next_user})   # обычная карточка

@login_required
@require_POST
def dislike_user_view(request, pk):

    from_user = request.user
    to_user = get_object_or_404(User, pk=pk)
    Dislike.objects.update_or_create(from_user=from_user, to_user=to_user)
    Like.objects.filter(from_user=from_user, to_user=to_user).delete()

    next_user = get_next_recommendation(from_user)
    return render(request, 'partials/user_card.html', {'recommended_user': next_user})

@login_required
def show_next_user_view(request):

    next_user = get_next_recommendation(request.user)
    return render(request, 'partials/user_card.html', {'recommended_user': next_user})