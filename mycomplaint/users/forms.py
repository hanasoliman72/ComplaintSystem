from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "Name", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.Role = "Student"  # Set default role to Student
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ["username", "password"]