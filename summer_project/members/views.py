from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm, ComplaintForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Complaint, Department, User, Response, _generate_tracking_code
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("members:student_dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            if user.Role == "Student":
                return redirect("members:student_dashboard")
            elif user.Role == "GeneralManager":
                return redirect("members:general_manager_dashboard")
            elif user.Role == "DepartmentManager":
                return redirect("members:department_manager_dashboard")
            else:
                return redirect("home")  # Fallback for unexpected roles
        else:
            # Handle invalid form
            return render(request, "login.html", {"form": form})
    else:
        form = CustomAuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "logout.html")

def student_dashboard(request):
    if not request.user.is_authenticated or request.user.Role != "Student":
        return redirect("home")
    return render(request, "student_dashboard.html", {"user": request.user})

def general_manager_dashboard(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return redirect("home")
    return render(request, "general_manager_dashboard.html", {"user": request.user})

def department_manager_dashboard(request):
    if not request.user.is_authenticated or request.user.Role != "DepartmentManager":
        return redirect("home")
    return render(request, "department_manager_dashboard.html", {"user": request.user})

def allComplaints_view(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return redirect("home")

    complaints = Complaint.objects.all().order_by("-CreatedDate")
    departments = Department.objects.all()

    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        department_id = request.POST.get("department_id")

        complaint = get_object_or_404(Complaint, pk=complaint_id)
        department = get_object_or_404(Department, pk=department_id)

        complaint.DepartmentId = department
        complaint.Status = "In Review"
        complaint.save()

        return redirect("members:allComplaints")

    return render(request, "allComplaints.html", {
        "complaints": complaints,
        "departments": departments,
    })

def departmentComplaints_view(request):
    if not request.user.is_authenticated or request.user.Role != "DepartmentManager":
        return redirect("home")

    complaints = Complaint.objects.filter(DepartmentId=request.user.DepartmentId, Status="In Review")

    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        message_text = request.POST.get("message_text")

        complaint = get_object_or_404(Complaint, pk=complaint_id)


        Response.objects.create(
            ComplaintId=complaint,
            SenderId=request.user,
            Message=message_text,
        )

        complaint.Status = "Resolved"
        complaint.save()

        messages.success(request, "Response recorded successfully.")
        return redirect('members:departmentComplaints')
    return render(request, "departmentComplaints.html", {
        "complaints": complaints,
    })

def submit_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.TrackingCode = _generate_tracking_code()
            complaint.save()
            return redirect('members:complaint_success')
    else:
        form = ComplaintForm()
    return render(request, 'submit_complaint.html', {'form': form})

def complaint_success(request):
    return render(request, 'success.html')