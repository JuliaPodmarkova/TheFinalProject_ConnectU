from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from ..forms import (UserRegistrationForm, UserEditForm, ProfileEditForm,
                     ProfilePreferencesForm)
from ..models import Interest


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, "Неверный email или пароль.")
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
    }
    return render(request, 'account/login.html', context)


def logout_view(request):
    logout(request)
    messages.info(request, "Вы успешно вышли из системы.")
    return redirect('home')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Регистрация прошла успешно! Добро пожаловать!")
            return redirect('profile_edit')
    else:
        form = UserRegistrationForm()

    return render(request, 'account/signup.html', {'form': form})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
        preferences_form = ProfilePreferencesForm(request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid() and preferences_form.is_valid():
            user_form.save()

            profile = profile_form.save(commit=False)
            other_interests_str = profile_form.cleaned_data.get('other_interests', '')
            if other_interests_str:
                current_interests = set(profile_form.cleaned_data.get('interests', []))
                interest_names = [name.strip().capitalize() for name in other_interests_str.split(',') if name.strip()]
                for name in interest_names:
                    interest, _ = Interest.objects.get_or_create(name=name)
                    current_interests.add(interest)
                profile_form.cleaned_data['interests'] = current_interests

            profile_form.save()
            profile_form.save_m2m()

            preferences_form.save()

            messages.success(request, 'Ваш профиль был успешно обновлен!')
            return redirect('profile_own')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        preferences_form = ProfilePreferencesForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'preferences_form': preferences_form,
    }
    return render(request, 'account/profile_edit.html', context)
