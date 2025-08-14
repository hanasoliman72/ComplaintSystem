import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

def _generate_tracking_code():
    for _ in range(10):
        code = uuid.uuid4().hex[:12].upper()
        if not Complaint.objects.filter(TrackingCode=code).exists():
            return code
    return uuid.uuid4().hex[:12].upper()


class Department(models.Model):
    DepartmentId = models.AutoField(primary_key=True)
    DepartmentName = models.CharField(max_length=255)

    def __str__(self):
        return self.DepartmentName


class User(AbstractUser):
    ROLE_CHOICES = [
        ("Student", "Student"),
        ("GeneralManager", "General Manager"),
        ("DepartmentManager", "Department Manager"),
    ]

    # primary key (replaces default id)
    UserId = models.AutoField(primary_key=True)

    # extra fields
    Name = models.CharField(max_length=255)
    GPA = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    # override email to make it unique (recommended). Do this before first migration.
    email = models.EmailField(unique=True)
    Role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Student")
    DepartmentId = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )

    # keep username as login field (change to "email" if you want email-login)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "Name", "Role"]

    def __str__(self):
        return f"{self.Name} ({self.Role})"


class Complaint(models.Model):
    TYPE_CHOICES = [
        ("Complaint", "Complaint"),
        ("Suggestion", "Suggestion"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Review", "In Review"),
        ("Resolved", "Resolved"),
    ]

    ComplaintId = models.AutoField(primary_key=True)
    TrackingCode = models.CharField(max_length=100, unique=True, blank=True)
    Type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    Title = models.CharField(max_length=255)
    Description = models.TextField()
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    DepartmentId = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="complaints"
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.Type} - {self.Title} ({self.TrackingCode})"


class Response(models.Model):
    ResponseId = models.AutoField(primary_key=True)
    ComplaintId = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="responses")
    SenderId = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="responses"
    )
    Message = models.TextField()
    ResponseDate = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.SenderId and self.SenderId.Role not in ("DepartmentManager", "GeneralManager"):
            raise ValidationError("Sender must be a DepartmentManager or GeneralManager")

    def __str__(self):
        return f"Response to {self.ComplaintId.TrackingCode}"


class ChatbotSession(models.Model):
    SessionId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")  # Must be a Student
    SessionStart = models.DateTimeField(auto_now_add=True)
    SessionEnd = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.UserId and self.UserId.Role != "Student":
            raise ValidationError("ChatbotSession.members must have role 'Student'")

    def __str__(self):
        return f"Session {self.SessionId} - {self.UserId.Name}"