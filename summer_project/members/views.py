from django.urls import reverse
from .forms import ComplaintForm
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.shortcuts import  get_object_or_404
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import Complaint, Department, Response, _generate_tracking_code

def RegisterView(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("members:student_dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})

def LoginView(request):
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

def LogoutView(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "logout.html")

def StudentDashboard(request):
    if not request.user.is_authenticated or request.user.Role != "Student":
        return redirect("home")
    return render(request, "student_dashboard.html", {"user": request.user})

def GeneralManagerDashboard(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return redirect("home")
    return render(request, "general_manager_dashboard.html", {"user": request.user})

def DepartmentManagerDashboard(request):
    if not request.user.is_authenticated or request.user.Role != "DepartmentManager":
        return redirect("home")
    return render(request, "department_manager_dashboard.html", {"user": request.user})

def AllComplaints(request):
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

        return redirect("members:all_complaints")

    return render(request, "all_complaints.html", {
        "complaints": complaints,
        "departments": departments,
    })

def DepartmentComplaints(request):
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
        return redirect('members:department_complaints')
    return render(request, "department_complaints.html", {
        "complaints": complaints,
    })

def SubmitComplaint(request):
    if not request.user.is_authenticated or request.user.Role != "Student":
        return redirect("home")

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.TrackingCode = _generate_tracking_code()
            complaint.save()

            # Send email with tracking code
            try:
                track_url = request.build_absolute_uri(
                    reverse('members:track_complaint') + f'?tracking_code={complaint.TrackingCode}')
                send_mail(
                    subject='Your Complaint Tracking Code',
                    message=(
                        f'Dear {request.user.Name},\n\n'
                        f'Your complaint has been submitted successfully. Please use the following tracking code to check the status of your complaint:\n\n'
                        f'Tracking Code: {complaint.TrackingCode}\n\n'
                        f'You can track your complaint at: {track_url}\n\n'
                        f'Thank you,\nYour University Team'
                    ),
                    from_email='hanasmsalah105@example.com',  # Replace with your sender email
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                messages.success(request,
                                 'Your complaint has been submitted, and the tracking code has been sent to your email.')
            except Exception as e:
                messages.error(request,
                               f'Your complaint was submitted, but there was an error sending the email: {str(e)}. Please contact support.')

            return redirect('members:success')
    else:
        form = ComplaintForm()
    return render(request, 'submit_complaint.html', {'form': form})

def Success(request):
    return render(request, 'success.html')

def GeneralManagerResponses(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return redirect("home")

    responses = Response.objects.select_related("ComplaintId", "SenderId").order_by("-ResponseDate")
    return render(request, "general_manager_responses.html", {"responses": responses})

def PublishResponse(request, response_id):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return redirect("home")

    response = get_object_or_404(Response, pk=response_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "publish":
            response.VisibleToStudent = True
            response.PublishedAt = timezone.now()
            response.save(update_fields=["VisibleToStudent", "PublishedAt"])
            messages.success(request, "Response published to student.")
        elif action == "unpublish":
            response.VisibleToStudent = False
            response.PublishedAt = None
            response.save(update_fields=["VisibleToStudent", "PublishedAt"])
            messages.success(request, "Response hidden from student.")

    return redirect("members:general_manager_responses")

def TrackComplaint(request):
    complaint = None
    tracking_code = request.GET.get("tracking_code", "").strip().upper()
    searched = False

    if tracking_code:
        searched = True
        complaint = Complaint.objects.filter(TrackingCode=tracking_code).first()

    return render(request, "track_complaint.html", {
        "complaint": complaint,
        "tracking_code": tracking_code,
        "searched": searched,
    })