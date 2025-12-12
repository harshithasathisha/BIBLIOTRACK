from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'favorite_genres', 'reading_preferences']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'favorite_genres': forms.Textarea(attrs={'placeholder': 'Enter genres as comma-separated values'}),
            'reading_preferences': forms.Textarea(attrs={'placeholder': 'Enter preferences as JSON'}),
        }

    def clean_favorite_genres(self):
        genres = self.cleaned_data.get('favorite_genres', '')
        if isinstance(genres, str):
            return [genre.strip() for genre in genres.split(',') if genre.strip()]
        return genres

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
