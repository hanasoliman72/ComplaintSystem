from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from members.models import User, Complaint

UserModel = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    Name = forms.CharField(max_length=255, required=True)

    class Meta:
        model = UserModel
        fields = (
            "username",
            "email",
            "Name",
            "GPA",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.Name = self.cleaned_data["Name"]
        user.GPA = self.cleaned_data["GPA"]
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['Type', 'Title', 'Description']
        widgets = {
            'Type': forms.Select(choices=Complaint.TYPE_CHOICES),
            'Title': forms.TextInput(attrs={'placeholder': 'Enter a title'}),
            'Description': forms.Textarea(attrs={'placeholder': 'Enter your complaint or suggestion'}),
        }

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ["username", "password"]

