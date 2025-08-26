import json
from pipes import quote
from .serializers import *
from rest_framework import status
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import  logout
from .models import _generate_tracking_code
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.shortcuts import  get_object_or_404
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from summer_project.settings import DEFAULT_FROM_EMAIL
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
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

@csrf_exempt
def LogoutView(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True, "message": "Logged out successfully"})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

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

@csrf_exempt
def SubmitComplaint(request):
    if request.method == "POST":
        if not request.user.is_authenticated or request.user.Role != "Student":
            return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

        complaint = Complaint.objects.create(
            Type=request.POST.get("type"),
            Title=request.POST.get("title"),
            Description=request.POST.get("description"),
            TrackingCode=_generate_tracking_code(),
            DepartmentId=request.user.DepartmentId
        )

        # save attachment
        files = request.FILES.getlist("file")
        for f in files:
            ComplaintAttachment.objects.create(complaint=complaint, file=f)


        # send email
        try:
            send_mail(
                subject="Your Complaint Tracking Code",
                message=(
                    f"Dear {request.user.Name},\n\n"
                    f"Your complaint has been submitted successfully.\n"
                    f"Tracking Code: {complaint.TrackingCode}\n"
                ),
                from_email="noreply@university.com",
                recipient_list=[request.user.email],
                fail_silently=False,
            )
        except Exception as e:
            return JsonResponse({"success": True, "tracking_code": complaint.TrackingCode, "email_error": str(e)})

        return JsonResponse({"success": True, "tracking_code": complaint.TrackingCode})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

@csrf_exempt
def TrackComplaint(request):
    tracking_code = request.GET.get("tracking_code")

    if not tracking_code:
        return JsonResponse({"error": "Tracking code is required"}, status=400)

    try:
        complaint = Complaint.objects.get(TrackingCode=tracking_code)
    except Complaint.DoesNotExist:
        return JsonResponse({"error": "Tracking code not found"}, status=404)

    # Collect visible responses
    responses = [
        {
            "message": r.Message,
            "date": r.ResponseDate.strftime("%Y-%m-%d %H:%M"),
        }
        for r in complaint.responses.filter(VisibleToStudent=True)
    ]

    data = {
        "status": complaint.Status,
        "type": complaint.Type,
        "title": complaint.Title,
        "description": complaint.Description,
        "created": complaint.CreatedDate.strftime("%b %d, %Y, %I:%M %p"),
        "trackingCode": complaint.TrackingCode,
        "responses": responses,
    }
    return JsonResponse(data)

@csrf_exempt
def password_reset_request(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            email = data.get("email")

            if not email:
                return JsonResponse({"success": False, "message": "Email is required"}, status=400)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({"success": True, "message": "If this email exists, a reset link will be sent."})  # Avoid revealing users

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://localhost:3000/reset-password/{quote(uid)}/{quote(token)}"

            # Send email
            send_mail(
                subject="Password Reset",
                message=f"Click here to reset your password: {reset_link}",
                from_email=DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return JsonResponse({"success": True, "message": "Password reset email sent"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Only POST method allowed"}, status=405)

@csrf_exempt
def password_reset_confirm(request, uidb64, token):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            password = data.get("password")

            if not password:
                return JsonResponse({"success": False, "message": "Password is required"}, status=400)

            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (User.DoesNotExist, ValueError, TypeError, OverflowError):
                return JsonResponse({"success": False, "message": "Invalid user"}, status=404)

            if not default_token_generator.check_token(user, token):
                return JsonResponse({"success": False, "message": "Invalid or expired token"}, status=400)

            user.set_password(password)
            user.save()

            return JsonResponse({"success": True, "message": "Password has been reset successfully"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Only POST method allowed"}, status=405)

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
