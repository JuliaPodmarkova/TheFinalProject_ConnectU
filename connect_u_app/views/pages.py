from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import UserProfile, Interest, User, Like, Dislike, Photo, Match, Message
from ..forms import UserEditForm, UserProfileEditForm, PhotoForm
from django.core.paginator import Paginator
from datetime import date
from ..forms import UserFilterForm


@login_required
def index(request):
    current_user = request.user

    # Базовый набор пользователей: активные, не суперюзеры, доступные для поиска, и не сам текущий пользователь
    base_users = User.objects.filter(
        is_active=True,
        is_superuser=False,
        profile__searchable=True
    ).exclude(pk=current_user.pk).select_related('profile')

    # Исключаем тех, с кем уже было взаимодействие (лайк/дизлайк)
    # Используем твою существующую логику с моделями Like и Dislike
    liked_users_ids = list(Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))
    disliked_users_ids = list(Dislike.objects.filter(from_user=current_user).values_list('to_user_id', flat=True))
    interacted_users_ids = set(liked_users_ids) | set(disliked_users_ids)

    recommended_users = base_users.exclude(id__in=interacted_users_ids)

    # --- ЛОГИКА ФИЛЬТРАЦИИ ---
    filter_form = UserFilterForm(request.GET)

    if filter_form.is_valid():
        gender = filter_form.cleaned_data.get('gender')
        min_age = filter_form.cleaned_data.get('min_age')
        max_age = filter_form.cleaned_data.get('max_age')
        city = filter_form.cleaned_data.get('city')

        if gender:
            recommended_users = recommended_users.filter(gender=gender)

        if city:
            recommended_users = recommended_users.filter(profile__city__icontains=city)

        today = date.today()
        if min_age:
            max_birth_date = today.replace(year=today.year - min_age)
            recommended_users = recommended_users.filter(birth_date__lte=max_birth_date)

        if max_age:
            min_birth_date = today.replace(year=today.year - (max_age + 1))
            recommended_users = recommended_users.filter(birth_date__gte=min_birth_date)

    # --- ПАГИНАЦИЯ ---
    paginator = Paginator(recommended_users.order_by('?'), 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Сохраняем GET-параметры фильтров для корректной работы пагинации
    filter_params = request.GET.copy()
    if 'page' in filter_params:
        del filter_params['page']

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'filter_params': filter_params.urlencode(),
    }
    return render(request, 'home.html', context)


@login_required
def profile_own_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    # Считаем лайки, дизлайки и мэтчи для текущего пользователя
    likes_given_count = Like.objects.filter(from_user=request.user).count()
    dislikes_given_count = Dislike.objects.filter(from_user=request.user).count()
    matches_count = Match.objects.filter(Q(user1=request.user) | Q(user2=request.user)).count()

    context = {
        'profile': profile,
        'likes_given_count': likes_given_count,
        'dislikes_given_count': dislikes_given_count,
        'matches_count': matches_count,
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

            selected_interests = set(profile_form.cleaned_data.get('interests', []))
            other_text = profile_form.cleaned_data.get('other_interests', '').strip()
            if other_text:
                interest_names = [name.strip().capitalize() for name in other_text.split(',') if name.strip()]
                for name in interest_names:
                    interest_obj, created = Interest.objects.get_or_create(name=name)
                    selected_interests.add(interest_obj)

            saved_profile = profile_form.save(commit=False)
            saved_profile.save()

            saved_profile.interests.set(list(selected_interests))

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
def search_view(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        results = UserProfile.objects.filter(
            full_name__icontains=query
        ).exclude(user=request.user)

    context = {
        'query': query,
        'results': results
    }
    return render(request, 'search.html', context)


@login_required
def match_list_view(request):
    matches_qs = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1__profile', 'user2__profile').order_by('-created_at')

    matches_list = []
    for match in matches_qs:
        if request.user == match.user1:
            match.other_user = match.user2
        else:
            match.other_user = match.user1
        matches_list.append(match)

    context = {
        'matches': matches_list
    }
    return render(request, 'matches.html', context)


@login_required
def chat_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if request.user != match.user1 and request.user != match.user2:
        return HttpResponseForbidden("У вас нет доступа к этому чату.")

    # ВОТ ЭТА СТРОКА БЫЛА СЛОМАНА. ТЕПЕРЬ ОНА ИСПРАВЛЕНА.
    other_user = match.user2 if request.user == match.user1 else match.user1

    messages = match.messages.all().select_related('sender__profile')

    context = {
        'match': match,
        'other_user': other_user,
        'messages': messages
    }
    return render(request, 'chat.html', context)


@login_required
def profile_view(request, user_id):
    """Отображает публичный профиль другого пользователя."""

    # Нельзя смотреть свой же профиль по этому URL, для этого есть profile_own
    if request.user.id == user_id:
        return redirect('profile_own')

    viewed_user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=viewed_user)

    # Проверяем, есть ли уже мэтч между пользователями
    is_match = Match.objects.filter(
        (Q(user1=request.user) & Q(user2=viewed_user)) |
        (Q(user1=viewed_user) & Q(user2=request.user))
    ).exists()

    context = {
        'profile': profile,
        'is_match': is_match,
    }
    return render(request, 'account/profile_public.html', context)
