from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import *
from django.urls import reverse
from .forms import ComplaintForm
from django.utils import timezone
from django.contrib import messages
from rest_framework.response import Response
from django.core.mail import send_mail
from .models import _generate_tracking_code
from django.shortcuts import render, redirect
from django.contrib.auth import  logout
from django.shortcuts import  get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
import json
from django.contrib.auth import get_user_model
User = get_user_model()

@api_view(["POST"])
def RegisterView(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def LoginView(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse({"success": False, "message": "Username and password required"}, status=400)

            # Authenticate user
            user = authenticate(request, username=username, password=password)
            if user is None:
                return JsonResponse({"success": False, "message": "Invalid credentials"}, status=400)

            # Login user (creates session)
            login(request, user)

            # Decide redirect/profile by Role
            role_redirects = {
                "Student": "/student/profile",
                "DepartmentManager": "/department_manager/profile",
                "GeneralManager": "/general_manager/profile",
            }
            profile_url = role_redirects.get(user.Role, "/")

            return JsonResponse({
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user.pk,  # Changed from user.id to user.pk
                    "username": user.username,
                    "email": user.email,
                    "role": user.Role,
                    "redirect": profile_url,
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Server error: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)


def LogoutView(request):
    if request.method == "POST":
        logout(request)
        return redirect("home")
    return render(request, "logout.html")


@csrf_exempt
def StudentProfile(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=401)

    if request.method == "GET":
        try:
            user = request.user
            return JsonResponse({
                "success": True,
                "user": {
                    "id": user.pk,
                    "name": user.Name,
                    "username": user.username,
                    "email": user.email,
                    "gpa": float(getattr(user, "GPA", 0)) if hasattr(user, "GPA") else None,
                }
            }, status=200)
        except Exception as e:
            print("ERROR in StudentDashboard GET:", e)
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    elif request.method == "PUT":
        try:
            data = json.loads(request.body.decode("utf-8"))
            user = request.user

            if "name" in data:
                user.first_name = data["name"]  # store in first_name
            if "username" in data:
                user.username = data["username"]

            user.save()

            return JsonResponse({
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "id": user.pk,
                    "name": user.Name,
                    "username": user.username,
                    "email": user.email,
                    "gpa": float(getattr(user, "GPA", 0)) if hasattr(user, "GPA") else None,
                }
            }, status=200)
        except Exception as e:
            print("ERROR in StudentDashboard PUT:", e)
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)


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

def submit_complaint(request):
    if not request.user.is_authenticated or request.user.Role != "Student":
        return redirect("home")

    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.TrackingCode = _generate_tracking_code()
            complaint.save()

            files = request.FILES.getlist("file")
            for f in files:
                ComplaintAttachment.objects.create(complaint=complaint, file=f)

            try:
                track_url = request.build_absolute_uri(
                    reverse('members:track_complaint') + f'?tracking_code={complaint.TrackingCode}'
                )
                send_mail(
                    subject='Your Complaint Tracking Code',
                    message=(
                        f'Dear {request.user.Name},\n\n'
                        f'Your complaint has been submitted successfully. Please use the following tracking code to check the status of your complaint:\n\n'
                        f'Tracking Code: {complaint.TrackingCode}\n\n'
                        f'You can track your complaint at: {track_url}\n\n'
                        f'Thank you,\nYour University Team'
                    ),
                    from_email='hanasmsalah105@example.com',
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                messages.success(request,
                                 'Your complaint has been submitted, and the tracking code has been sent to your email.')
            except Exception as e:
                messages.error(request,
                               f'Your complaint was submitted, but there was an error sending the email: {str(e)}. Please contact support.')

            return redirect("members:success")
    else:
        form = ComplaintForm()

    return render(request, "submit_complaint.html", {"form": form})

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

