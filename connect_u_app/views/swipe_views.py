from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from ..models import User, UserProfile, Like, Dislike, Match
from datetime import date
import json


def get_next_candidate_for_user(current_user):
    liked_user_ids = Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True)
    disliked_user_ids = Dislike.objects.filter(from_user=current_user).values_list('to_user_id', flat=True)
    interacted_user_ids = set(liked_user_ids) | set(disliked_user_ids)

    candidates = User.objects.exclude(id=current_user.id).exclude(id__in=interacted_user_ids).filter(
        profile__searchable=True, is_active=True)

    try:
        preferences = current_user.profile
        if preferences:
            if preferences.search_gender:
                candidates = candidates.filter(gender=preferences.search_gender)

            today = date.today()
            if preferences.search_min_age:
                max_birth_date = today.replace(year=today.year - preferences.search_min_age)
                candidates = candidates.filter(birth_date__lte=max_birth_date)
            if preferences.search_max_age:
                min_birth_date = today.replace(year=today.year - (preferences.search_max_age + 1))
                candidates = candidates.filter(birth_date__gte=min_birth_date)

    except UserProfile.DoesNotExist:
        pass

    return candidates.order_by('?').first()


@login_required
def swipe_view(request):

    candidate = get_next_candidate_for_user(request.user)
    context = {'candidate': candidate}
    return render(request, 'swipe/main.html', context)


@login_required
def process_swipe(request):

    if request.method == 'POST':
        swiped_user_id = request.POST.get('swiped_user_id')
        action = request.POST.get('action')

        swiped_user = get_object_or_404(User, id=swiped_user_id)
        current_user = request.user

        is_match = False

        if action == 'like':
            Like.objects.get_or_create(from_user=current_user, to_user=swiped_user)
            if Like.objects.filter(from_user=swiped_user, to_user=current_user).exists():
                is_match = True
                Match.objects.get_or_create(
                    user1=min(current_user, swiped_user, key=lambda u: u.id),
                    user2=max(current_user, swiped_user, key=lambda u: u.id)
                )

        elif action == 'dislike':
            Dislike.objects.get_or_create(from_user=current_user, to_user=swiped_user)

        next_candidate = get_next_candidate_for_user(current_user)

        context = {'candidate': next_candidate}
        response = render(request, 'swipe/card.html', context)

        if is_match:
            match_data = {
                "matchName": swiped_user.profile.full_name,
                "matchAvatarUrl": swiped_user.profile.get_avatar_url()
            }
            response['HX-Trigger'] = json.dumps({'matchOccurred': match_data})

        return response
    return redirect('swipe')
