from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from ..models import UserProfile, Interest, User, Like, Dislike
from ..forms import UserEditForm, UserProfileEditForm


@login_required
def index(request):
    current_user = request.user

    interacted_users_ids = list(Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))
    interacted_users_ids += list(Dislike.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))

    recommended_user = User.objects.exclude(
        Q(id=current_user.id) | Q(id__in=interacted_users_ids)
    ).order_by('?').first()  # '?' - случайный порядок, first() - берем первого

    context = {
        'recommended_user': recommended_user
    }
    return render(request, 'home.html', context)


@login_required
def profile_own_view(request):
    # Используем get_object_or_404 для надежности
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

            saved_profile = profile_form.save()

            other_text = profile_form.cleaned_data.get('other_interests', '').strip()
            if other_text:
                interest_names = [name.strip().capitalize() for name in other_text.split(',') if name.strip()]
                for name in interest_names:
                    interest_obj, created = Interest.objects.get_or_create(name=name)
                    saved_profile.interests.add(interest_obj)

            messages.success(request, 'Ваши изменения успешно сохранены!')
            return redirect('profile_own')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме. Они подсвечены красным.')

    else:
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileEditForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'account/profile_edit.html', context)