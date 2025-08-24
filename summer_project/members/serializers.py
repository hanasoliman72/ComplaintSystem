from rest_framework import serializers
from .models import *

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            "DepartmentName",
            "DepartmentName"
        ]

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "UserId",
            "username",
            "Name",
            "GPA",
            "email",
            "Role",
            "password",
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            Name=validated_data.get("Name"),
            email=validated_data.get("email"),
            GPA=validated_data.get("GPA", 0),
            Role=validated_data.get("Role", "Student"),
        )
        return user

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            "ComplaintId",
            "TrackingCode",
            "Type",
            "Title",
            "Description",
            "Status",
            "DepartmentId",
        ]

class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintAttachment
        fields = [
            "complaint",
            "file",
            "uploaded_at",
        ]

class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = [
            "ResponseId",
            "ComplaintId",
            "SenderId",
            "Message",
            "ResponseDate",
            "VisibleToStudent",
            "PublishedAt",
        ]

class ChatbotSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotSession
        fields = [
            "SessionId",
            "UserId",
            "SessionStart",
            "SessionEnd",
            "LastActivityAt",
            "kommunicate_conversation_id"
        ]
