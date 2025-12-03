from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, Interest, Photo
from datetime import date

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """Форма для регистрации нового пользователя."""
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True, label="Пол")
    birth_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}), label="Дата рождения")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'gender', 'birth_date')


class UserEditForm(forms.ModelForm):
    """Форма для редактирования данных пользователя, хранящихся в модели User."""

    class Meta:
        model = User
        fields = ('email', 'gender', 'birth_date')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].widget = forms.DateInput(attrs={'type': 'date'})
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class UserProfileEditForm(forms.ModelForm):
    """Форма для редактирования данных профиля пользователя (UserProfile)."""
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Ваши интересы"
    )

    other_interests = forms.CharField(
        required=False,
        label="Другие интересы (через запятую)",
        widget=forms.TextInput(attrs={'placeholder': 'Йога, Путешествия, Программирование'})
    )

    class Meta:
        model = UserProfile
        # ИЗМЕНЕНИЕ: Добавили новые поля в список
        fields = (
            'full_name', 'avatar', 'city', 'bio', 'status',
            'interests', 'other_interests',
            'show_age', 'show_city', 'searchable'
        )
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'avatar': forms.ClearableFileInput(),
        }
        # НОВОЕ: Добавляем красивые подписи для полей приватности
        labels = {
            'show_age': 'Показывать мой возраст другим пользователям',
            'show_city': 'Показывать мой город в профиле',
            'searchable': 'Разрешить другим пользователям находить меня через поиск'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ИЗМЕНЕНИЕ: Улучшенная логика для автоматического добавления CSS-классов
        for field_name, field in self.fields.items():
            # Для переключателей (настройки приватности)
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input', 'role': 'switch'})
            # Для выпадающих списков (статус)
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            # Для чекбоксов интересов
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-check-input'})
            # Пропускаем поле загрузки файла
            elif not isinstance(field.widget, forms.ClearableFileInput):
                # Для всех остальных (текстовые поля, textarea)
                field.widget.attrs.update({'class': 'form-control'})


class PhotoForm(forms.ModelForm):
    """Форма для загрузки новой фотографии в галерею."""

    class Meta:
        model = Photo
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'image': 'Выберите фото для загрузки'
        }


class UserFilterForm(forms.Form):
    """Форма для фильтрации пользователей в ленте."""
    GENDER_CHOICES = (
        ('', 'Не важно'),  # Пустой вариант
        ('M', 'Мужчин'),
        ('F', 'Женщин'),
    )

    # Мы используем CharField, чтобы легко добавить 'Не важно'
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        label="Показывать"
    )
    min_age = forms.IntegerField(
        required=False,
        min_value=18,
        label="Возраст от",
        widget=forms.NumberInput(attrs={'placeholder': '18'})
    )
    max_age = forms.IntegerField(
        required=False,
        min_value=18,
        label="до",
        widget=forms.NumberInput(attrs={'placeholder': '99'})
    )
    city = forms.CharField(
        required=False,
        label="Город",
        widget=forms.TextInput(attrs={'placeholder': 'Например, Москва'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем стили Bootstrap
        self.fields['gender'].widget.attrs.update({'class': 'form-select'})
        self.fields['min_age'].widget.attrs.update({'class': 'form-control'})
        self.fields['max_age'].widget.attrs.update({'class': 'form-control'})
        self.fields['city'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')

        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError("Минимальный возраст не может быть больше максимального.")

        return cleaned_data


class UserFilterForm(forms.Form):
    """Форма для фильтрации пользователей в ленте."""
    GENDER_CHOICES = (
        ('', 'Не важно'),  # Пустой вариант
        ('M', 'Мужчин'),
        ('F', 'Женщин'),
    )

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        label="Показывать"
    )
    min_age = forms.IntegerField(
        required=False,
        min_value=18,
        label="Возраст от",
        widget=forms.NumberInput(attrs={'placeholder': '18'})
    )
    max_age = forms.IntegerField(
        required=False,
        min_value=18,
        label="до",
        widget=forms.NumberInput(attrs={'placeholder': '99'})
    )
    city = forms.CharField(
        required=False,
        label="Город",
        widget=forms.TextInput(attrs={'placeholder': 'Например, Москва'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем стили Bootstrap
        self.fields['gender'].widget.attrs.update({'class': 'form-select'})
        self.fields['min_age'].widget.attrs.update({'class': 'form-control'})
        self.fields['max_age'].widget.attrs.update({'class': 'form-control'})
        self.fields['city'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')

        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError("Минимальный возраст не может быть больше максимального.")

        return cleaned_data