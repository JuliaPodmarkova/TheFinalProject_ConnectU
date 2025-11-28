# connect_u_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Interest

class UserRegistrationForm(UserCreationForm): # <--- ВОТ ИЗМЕНЕНИЕ
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем класс 'form-control' ко всем полям формы
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class UserProfileEditForm(forms.ModelForm):
    # Поле для интересов из чекбоксов
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Интересы"
    )
    # Поле для ввода новых интересов текстом
    other_interests = forms.CharField(
        required=False,
        label="Другие интересы (через запятую)",
        help_text="Например: Йога, Путешествия, Программирование"
    )

    class Meta:
        model = UserProfile
        # Убираем 'interests' из fields, т.к. мы его определили выше вручную
        fields = ('full_name', 'city', 'bio', 'avatar', 'interests', 'other_interests')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем класс 'form-control' ко всем полям, кроме чекбоксов
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})