from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Admission, CallTranscript, Employee, FollowUp, Lead, LeadActivity, Meeting, Office, Prediction


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ["id", "name", "city", "state", "monthly_expense", "active"]


class EmployeeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True)

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    class Meta:
        model = Employee
        fields = [
            "id", "name", "username", "email", "role", "phone",
            "office", "office_name", "active",
        ]


class SignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=Employee.ROLE_CHOICES)
    office = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.filter(active=True),
        required=False,
        allow_null=True,
    )
    admin_signup_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs):
        role = attrs["role"]
        office = attrs.get("office")

        if role in [Employee.MANAGER, Employee.COUNSELLOR] and not office:
            raise serializers.ValidationError({"office": "Office is required for this role."})

        # Leadership is global and is not attached to one branch.
        if role == Employee.ADMIN:
            attrs["office"] = None

        return attrs


class LeadSerializer(serializers.ModelSerializer):
    office_name = serializers.CharField(source="office.name", read_only=True)
    manager_name = serializers.SerializerMethodField()
    counsellor_name = serializers.SerializerMethodField()
    latest_prediction = serializers.SerializerMethodField()

    def get_manager_name(self, obj):
        if not obj.assigned_manager:
            return None
        return obj.assigned_manager.user.get_full_name() or obj.assigned_manager.user.username

    def get_counsellor_name(self, obj):
        if not obj.assigned_counsellor:
            return None
        return obj.assigned_counsellor.user.get_full_name() or obj.assigned_counsellor.user.username

    def get_latest_prediction(self, obj):
        prediction = obj.predictions.order_by("-created_at").first()
        return PredictionSerializer(prediction).data if prediction else None

    class Meta:
        model = Lead
        fields = "__all__"
        read_only_fields = ["created_by", "office"]


class LeadActivitySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        if not obj.employee:
            return "System"
        return obj.employee.user.get_full_name() or obj.employee.user.username

    class Meta:
        model = LeadActivity
        fields = "__all__"
        read_only_fields = ["employee"]


class FollowUpSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="lead.student_name", read_only=True)

    class Meta:
        model = FollowUp
        fields = "__all__"


class AdmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admission
        fields = "__all__"


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = "__all__"


class CallTranscriptSerializer(serializers.ModelSerializer):
    counsellor_name = serializers.SerializerMethodField()

    def get_counsellor_name(self, obj):
        if not obj.counsellor:
            return "Unknown"
        return obj.counsellor.user.get_full_name() or obj.counsellor.user.email

    class Meta:
        model = CallTranscript
        fields = "__all__"
        read_only_fields = ["counsellor"]


class MeetingSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="lead.student_name", read_only=True)
    student_email = serializers.CharField(source="lead.email", read_only=True)
    counsellor_name = serializers.SerializerMethodField()

    def get_counsellor_name(self, obj):
        return obj.counsellor.user.get_full_name() or obj.counsellor.user.email

    class Meta:
        model = Meeting
        fields = "__all__"
        read_only_fields = ["counsellor", "meeting_url", "invitation_sent"]
