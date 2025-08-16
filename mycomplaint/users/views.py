from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("users:student_dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            if user.Role == "Student":
                return redirect("users:student_dashboard")
            elif user.Role == "GeneralManager":
                return redirect("users:gm_dashboard")
            elif user.Role == "DepartmentManager":
                return redirect("users:dm_dashboard")
            else:
                return redirect("home")  # Fallback for unexpected roles
        else:
            # Handle invalid form
            return render(request, "users/login.html", {"form": form})
    else:
        form = CustomAuthenticationForm()
    return render(request, "users/login.html", {"form": form})

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "users/logout.html")

def student_dashboard(request):
    if not request.user.is_authenticated or request.user.Role != "Student":
        return redirect("home")
    return render(request, "users/student_dashboard.html", {"user": request.user})

def gm_dashboard(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return redirect("home")
    return render(request, "users/gm_dashboard.html", {"user": request.user})

def dm_dashboard(request):
    if not request.user.is_authenticated or request.user.Role != "DepartmentManager":
        return redirect("home")
    return render(request, "users/dm_dashboard.html", {"user": request.user})