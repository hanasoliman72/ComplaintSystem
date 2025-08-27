import json
from pipes import quote
from .serializers import *
from rest_framework import status
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import logout
from .models import _generate_tracking_code, Response
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from summer_project.settings import DEFAULT_FROM_EMAIL
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.response import Response

User = get_user_model()


@api_view(["POST"])
@csrf_exempt
def RegisterView(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")
            name = data.get("Name")
            email = data.get("email")
            gpa = data.get("GPA", 0)
            role = data.get("role", "Student")

            # Basic validation
            if not username or not password:
                return JsonResponse({"success": False, "message": "Username and password required"}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"success": False, "message": "Username already taken"}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({"success": False, "message": "Email already registered"}, status=400)

            # Create the user (using create_user so password is hashed)
            user = User.objects.create_user(
                username=username,
                password=password,
                Name=name,
                email=email,
                GPA=gpa,
                Role=role
            )

            return JsonResponse({
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "id": user.pk,
                    "username": user.username,
                    "email": user.email,
                    "name": user.Name,
                    "gpa": user.GPA,
                    "role": user.Role
                }
            }, status=201)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Server error: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)


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
            print("ERROR in StudentProfile GET:", e)
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
                return JsonResponse({"success": True,
                                     "message": "If this email exists, a reset link will be sent."})  # Avoid revealing users

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


@csrf_exempt
def GeneralManagerProfile(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
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
                }
            }, status=200)
        except Exception as e:
            print("ERROR in GeneralManagerProfile GET:", e)
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)


@csrf_exempt
def AllComplaints(request):
    if request.method == "GET":
        complaints = Complaint.objects.all().select_related("DepartmentId").prefetch_related("attachments")

        data = []
        for complaint in complaints:
            data.append({
                "ComplaintId": complaint.ComplaintId,
                "TrackingCode": complaint.TrackingCode,
                "Type": complaint.Type,
                "Title": complaint.Title,
                "Description": complaint.Description,
                "Status": complaint.Status,
                "Department": complaint.DepartmentId.DepartmentName if complaint.DepartmentId else None,
                "CreatedDate": complaint.CreatedDate.strftime("%Y-%m-%d %H:%M"),
                "Attachments": [
                    request.build_absolute_uri(att.file.url) if att.file else None
                    for att in complaint.attachments.all()
                ],
            })

        departments = Department.objects.all()
        departments_data = [
            {"DepartmentId": d.pk, "DepartmentName": d.DepartmentName}
            for d in departments
        ]
        return JsonResponse({
            "complaints": data,
            "departments": departments_data
        })

    elif request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            complaint_id = body.get("ComplaintId")
            department_id = body.get("DepartmentId")

            complaint = Complaint.objects.get(ComplaintId=complaint_id)
            department = Department.objects.get(pk=department_id)

            complaint.DepartmentId = department
            complaint.Status = "In Review"
            complaint.save()

            return JsonResponse({"success": True, "message": "Complaint assigned successfully"})
        except Complaint.DoesNotExist:
            return JsonResponse({"error": "Complaint not found"}, status=404)
        except Department.DoesNotExist:
            return JsonResponse({"error": "Department not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def GeneralManagerResponses(request):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    responses = Response.objects.select_related("ComplaintId", "SenderId").order_by("-ResponseDate")

    data = [
        {
            "id": r.pk,
            "complaintTitle": r.ComplaintId.Title,
            "responseMessage": r.Message,
            "senderDepartment": r.SenderId.DepartmentId.DepartmentName,
            "responseDate": r.ResponseDate.strftime("%Y-%m-%d"),
            "visible": r.VisibleToStudent,
        }
        for r in responses
    ]
    return JsonResponse(data, safe=False)


@csrf_exempt
def PublishResponse(request, response_id):
    if not request.user.is_authenticated or request.user.Role != "GeneralManager":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    response = get_object_or_404(Response, pk=response_id)

    if request.method == "POST":
        try:
            import json
            body = json.loads(request.body.decode("utf-8"))
            new_visible = body.get("visible", None)

            if new_visible is None:
                return JsonResponse({"error": "Missing 'visible' field"}, status=400)

            if new_visible:
                response.VisibleToStudent = True
                response.PublishedAt = timezone.now()
                msg = "Response published to student."
            else:
                response.VisibleToStudent = False
                response.PublishedAt = None
                msg = "Response hidden from student."

            response.save(update_fields=["VisibleToStudent", "PublishedAt"])

            return JsonResponse({
                "id": response.pk,
                "complaintTitle": response.ComplaintId.Title,
                "responseMessage": response.Message,
                "senderDepartment": response.SenderId.DepartmentId.DepartmentName,
                "responseDate": response.ResponseDate.strftime("%Y-%m-%d"),
                "visible": response.VisibleToStudent,
                "message": msg,
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def DepartmentManagerProfile(request):
    if not request.user.is_authenticated or request.user.Role != "DepartmentManager":
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
                    "role": user.Role,
                    "department": user.DepartmentId.DepartmentName if user.DepartmentId else None,
                    "department_id": user.DepartmentId_id,
                }
            }, status=200)
        except Exception as e:
            print("ERROR in DepartmentManagerProfile GET:", e)
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)


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
