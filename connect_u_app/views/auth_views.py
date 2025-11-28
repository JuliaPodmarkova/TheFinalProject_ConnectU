# connect_u_app/views/auth_views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from ..models import User
from ..forms import UserRegistrationForm


def login_view(request):
    """
    Обрабатывает вход пользователя.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Неверное имя пользователя или пароль.")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = AuthenticationForm()

    return render(request, 'account/login.html', {'form': form})


def logout_view(request):
    """
    Обрабатывает выход пользователя.
    """
    logout(request)
    return redirect('home')


def register_view(request):
    """
    Обрабатывает регистрацию нового пользователя.
    (Это твоя функция signup_view, переименована для единообразия).
    """
    if request.user.is_authenticated:
        return redirect('home')  # Перенаправляем на ленту, если уже вошел

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Используем create_user для правильного сохранения пароля
            new_user = User.objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                gender=form.cleaned_data['gender'],
                birth_date=form.cleaned_data['birth_date']
            )
            # Профиль создается автоматически сигналом, мы его просто дополняем
            new_user.profile.full_name = form.cleaned_data['full_name']
            new_user.profile.city = form.cleaned_data['city']
            new_user.profile.save()

            login(request, new_user)
            messages.success(request, "Регистрация прошла успешно! Добро пожаловать!")
            return redirect('home')  # Перенаправляем на ленту после регистрации
    else:
        form = UserRegistrationForm()

    return render(request, 'account/signup.html', {'form': form})