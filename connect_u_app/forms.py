from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, Interest

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True, label="Пол")
    birth_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}), label="Дата рождения")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'gender', 'birth_date')

class UserEditForm(forms.ModelForm):
    # Явно добавляем поля, чтобы управлять ими
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=True, label="Пол")
    birth_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}), label="Дата рождения")

    class Meta:
        model = User
        # Добавляем новые поля сюда!
        fields = ('email', 'gender', 'birth_date')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class UserProfileEditForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Интересы"
    )
    other_interests = forms.CharField(
        required=False,
        label="Другие интересы (через запятую)",
        help_text="Например: Йога, Путешествия, Программирование"
    )

    class Meta:
        model = UserProfile
        fields = ('full_name', 'city', 'bio', 'avatar', 'interests', 'other_interests')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})