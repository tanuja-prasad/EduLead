import os

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Admission, Employee, FollowUp, Lead, LeadActivity, Office, Prediction
from .serializers import (
    AdmissionSerializer,
    EmployeeSerializer,
    FollowUpSerializer,
    LeadActivitySerializer,
    LeadSerializer,
    OfficeSerializer,
    PredictionSerializer,
    SignupSerializer,
)
from .services.dashboard_service import employee_performance, monthly_revenue, office_performance
from .services.ml_service import predict_lead


def current_employee(request):
    return getattr(request.user, "employee", None)


def user_payload(user):
    employee = user.employee
    return {
        "id": user.id,
        "username": user.username,
        "name": user.get_full_name() or user.username,
        "email": user.email,
        "role": employee.role,
        "office_id": employee.office_id,
        "office": employee.office.name if employee.office else "All Offices",
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def public_offices(request):
    offices = Office.objects.filter(active=True).order_by("name")
    return Response(OfficeSerializer(offices, many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if data["role"] == Employee.ADMIN:
        expected_code = os.getenv("ADMIN_SIGNUP_CODE", "")
        supplied_code = data.get("admin_signup_code", "")
        if not expected_code or supplied_code != expected_code:
            return Response(
                {"detail": "A valid organization admin signup code is required."},
                status=status.HTTP_403_FORBIDDEN,
            )

    with transaction.atomic():
        # Keep Django's standard User model simple: the email is also used
        # internally as the username, while the UI remains email-only.
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
        )
        Employee.objects.create(
            user=user,
            office=data.get("office"),
            role=data["role"],
            phone=data.get("phone", ""),
        )

    return Response({"detail": "Account created successfully."}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")

    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Email uniquely identifies the employee. Role and office are read from
    # Employee, so users never choose them on the sign-in screen.
    django_user = User.objects.filter(email__iexact=email).first()
    if not django_user:
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user = authenticate(username=django_user.username, password=password)
    if not user or not hasattr(user, "employee"):
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    employee = user.employee
    if not employee.active:
        return Response(
            {"detail": "This account is inactive."},
            status=status.HTTP_403_FORBIDDEN,
        )

    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": user_payload(user),
    })


@api_view(["GET"])
def me(request):
    return Response(user_payload(request.user))


class OfficeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Office.objects.filter(active=True).order_by("name")
    serializer_class = OfficeSerializer


class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        employee = current_employee(self.request)
        queryset = Employee.objects.select_related("user", "office").filter(active=True)

        if employee.role == Employee.ADMIN:
            return queryset
        return queryset.filter(office=employee.office)


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["student_name", "phone", "email", "course", "country"]

    def get_queryset(self):
        employee = current_employee(self.request)
        queryset = Lead.objects.select_related(
            "office",
            "assigned_manager__user",
            "assigned_counsellor__user",
        ).order_by("-created_at")

        if employee.role == Employee.MANAGER:
            queryset = queryset.filter(office=employee.office)
        elif employee.role == Employee.COUNSELLOR:
            queryset = queryset.filter(assigned_counsellor=employee)

        lead_status = self.request.query_params.get("status")
        source = self.request.query_params.get("source")
        if lead_status:
            queryset = queryset.filter(status=lead_status)
        if source:
            queryset = queryset.filter(source=source)

        return queryset

    def perform_create(self, serializer):
        employee = current_employee(self.request)

        # Managers create direct/walk-in leads only for their own branch.
        # The office is never trusted from the browser.
        if employee.role == Employee.MANAGER:
            if not employee.office:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"office": "Your manager account is not assigned to an office."})
            office = employee.office
            assigned_manager = employee
        elif employee.role == Employee.ADMIN:
            # Admin lead creation is not exposed in the current UI. Keep a
            # deterministic office if an admin uses this endpoint directly.
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "Create leads from a branch manager account so the office is assigned automatically."})
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only managers can manually create leads.")

        lead = serializer.save(
            office=office,
            assigned_manager=assigned_manager,
            created_by=self.request.user,
        )
        LeadActivity.objects.create(
            lead=lead,
            employee=employee,
            activity_type="CREATED",
            remark="Lead created",
        )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        employee = current_employee(request)
        if employee.role != Employee.MANAGER:
            return Response({"detail": "Only a manager can assign leads."}, status=403)

        lead = self.get_object()
        counsellor_id = request.data.get("counsellor_id")
        counsellor = Employee.objects.filter(
            id=counsellor_id,
            role=Employee.COUNSELLOR,
            office=employee.office,
            active=True,
        ).first()

        if not counsellor:
            return Response({"detail": "Counsellor not found in your office."}, status=400)

        lead.assigned_manager = employee
        lead.assigned_counsellor = counsellor
        lead.save(update_fields=["assigned_manager", "assigned_counsellor", "updated_at"])

        LeadActivity.objects.create(
            lead=lead,
            employee=employee,
            activity_type="ASSIGNED",
            remark=f"Assigned to {counsellor.user.get_full_name() or counsellor.user.username}",
        )
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=["get", "post"])
    def history(self, request, pk=None):
        lead = self.get_object()
        employee = current_employee(request)

        if request.method == "POST":
            LeadActivity.objects.create(
                lead=lead,
                employee=employee,
                activity_type=request.data.get("activity_type", "REMARK"),
                remark=request.data.get("remark", ""),
            )

        history = lead.activities.select_related("employee__user").order_by("-created_at")
        return Response(LeadActivitySerializer(history, many=True).data)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        lead = self.get_object()
        employee = current_employee(request)
        new_status = request.data.get("status")
        valid_statuses = dict(Lead.STATUS_CHOICES)

        if new_status not in valid_statuses:
            return Response({"detail": "Invalid lead status."}, status=400)

        old_status = lead.status
        lead.status = new_status
        lead.save(update_fields=["status", "updated_at"])

        LeadActivity.objects.create(
            lead=lead,
            employee=employee,
            activity_type="STATUS",
            old_status=old_status,
            new_status=new_status,
            remark=request.data.get("remark", ""),
        )
        return Response(LeadSerializer(lead).data)

    @action(detail=True, methods=["post"])
    def predict(self, request, pk=None):
        lead = self.get_object()
        result = predict_lead(lead)
        prediction = Prediction.objects.create(
            lead=lead,
            admission_probability=result["probability"],
            priority=result["priority"],
            expected_revenue=result["expected_revenue"],
            model_version=result["model_version"],
        )
        return Response(PredictionSerializer(prediction).data)


class FollowUpViewSet(viewsets.ModelViewSet):
    serializer_class = FollowUpSerializer

    def get_queryset(self):
        employee = current_employee(self.request)
        queryset = FollowUp.objects.select_related("lead", "counsellor__user").order_by("followup_at")

        if employee.role == Employee.COUNSELLOR:
            return queryset.filter(counsellor=employee)
        if employee.role == Employee.MANAGER:
            return queryset.filter(lead__office=employee.office)
        return queryset

    def perform_create(self, serializer):
        employee = current_employee(self.request)
        counsellor = employee if employee.role == Employee.COUNSELLOR else serializer.validated_data["counsellor"]
        serializer.save(counsellor=counsellor)


class AdmissionViewSet(viewsets.ModelViewSet):
    serializer_class = AdmissionSerializer

    def get_queryset(self):
        employee = current_employee(self.request)
        queryset = Admission.objects.select_related("lead", "lead__office")
        if employee.role == Employee.ADMIN:
            return queryset
        return queryset.filter(lead__office=employee.office)


@api_view(["GET"])
def dashboard(request):
    employee = current_employee(request)
    leads = Lead.objects.all()

    if employee.role == Employee.MANAGER:
        leads = leads.filter(office=employee.office)
    elif employee.role == Employee.COUNSELLOR:
        leads = leads.filter(assigned_counsellor=employee)

    total = leads.count()
    admissions = Admission.objects.filter(lead__in=leads)
    admission_count = admissions.count()
    revenue = admissions.aggregate(total=Sum("revenue"))["total"] or 0

    expected_revenue = 0
    expected_admissions = 0
    priority = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for lead in leads.exclude(status__in=["ENROLLED", "LOST"]):
        prediction = lead.predictions.order_by("-created_at").first()
        if prediction:
            expected_revenue += float(prediction.expected_revenue)
            expected_admissions += prediction.admission_probability / 100
            priority[prediction.priority] = priority.get(prediction.priority, 0) + 1

    response = {
        "total_leads": total,
        "new_leads": leads.filter(status="NEW").count(),
        "active_pipeline": leads.exclude(status__in=["ENROLLED", "LOST"]).count(),
        "followups_due": FollowUp.objects.filter(lead__in=leads, completed=False, followup_at__lte=timezone.now() + timezone.timedelta(days=1)).count(),
        "admissions": admission_count,
        "conversion_rate": round(admission_count * 100 / total, 1) if total else 0,
        "total_revenue": float(revenue),
        "expected_admissions": round(expected_admissions, 1),
        "expected_revenue": round(expected_revenue, 2),
        "lead_priority": priority,
        "source_performance": list(
            leads.values("source")
            .annotate(total=Count("id"), converted=Count("id", filter=Q(status="ENROLLED")))
            .order_by("-converted", "-total")
        ),
    }

    if employee.role == Employee.ADMIN:
        offices = office_performance()
        total_expense = sum(row["monthly_expense"] for row in offices)
        response.update({
            "office_performance": offices,
            "monthly_revenue": monthly_revenue(),
            "manager_performance": employee_performance(Employee.MANAGER),
            "counsellor_performance": employee_performance(Employee.COUNSELLOR),
            "projected_profit": round(float(revenue) + expected_revenue - total_expense, 2),
        })

    return Response(response)
