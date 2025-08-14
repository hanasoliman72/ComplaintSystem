from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
UserModel = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    Name = forms.CharField(max_length=255)

    class Meta:
        model = UserModel
        fields = ("username", "email", "Name", "GPA", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.Name = self.cleaned_data["Name"]
        user.GPA = self.cleaned_data["GPA"]
        if commit:
            user.save()
        return user
