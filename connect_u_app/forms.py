from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile, Interest, Photo

class UserRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'gender', 'birth_date')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})

class UserProfileEditForm(forms.ModelForm):
    other_interests = forms.CharField(
        label="Другие интересы (через запятую)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Музыка, путешествия, спорт'})
    )
    class Meta:
        model = UserProfile
        fields = (
            'full_name', 'city', 'bio', 'interests', 'status',
            'search_gender', 'search_min_age', 'search_max_age',
            'show_age', 'show_city', 'searchable'
        )
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'interests': forms.CheckboxSelectMultiple,
            'search_gender': forms.Select(attrs={'class': 'form-select'}),
            'search_min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'search_max_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'show_age': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_city': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'searchable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['interests'].queryset = Interest.objects.all()
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets:
                field.widget.attrs.update({'class': 'form-control'})

class ProfilePreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'search_gender',
            'search_min_age',
            'search_max_age',
            'show_age',
            'show_city',
            'searchable'
        ]
        widgets = {
            'search_gender': forms.Select(attrs={'class': 'form-select'}),
            'search_min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'search_max_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'show_age': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_city': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'searchable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'is_main']
        labels = {
            'image': 'Выберите файл',
            'is_main': 'Сделать главным фото'
        }
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UserFilterForm(forms.Form):
    gender = forms.ChoiceField(
        choices=(('', 'Любой'),) + User.GENDER_CHOICES,
        required=False,
        label="Пол",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_age = forms.IntegerField(
        required=False,
        label="Возраст от",
        min_value=18,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '18'})
    )
    max_age = forms.IntegerField(
        required=False,
        label="до",
        min_value=18,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '99'})
    )
    city = forms.CharField(
        required=False,
        label="Город",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название города'})
    )
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated and hasattr(user, 'profile'):
            self.fields['gender'].initial = user.profile.search_gender
            self.fields['min_age'].initial = user.profile.search_min_age
            self.fields['max_age'].initial = user.profile.search_max_age