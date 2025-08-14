from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("/")
        else:
            print("Form errors:", form.errors)  # Debugging
            return render(request, 'members/register.html', {"form": form})
    else:
        form = CustomUserCreationForm()
        return render(request, 'members/register.html', {"form": form})
