import os
import uuid
from datetime import timedelta, timezone as dt_timezone

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

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

from .models import Admission, CallTranscript, Employee, FollowUp, Lead, LeadActivity, Meeting, Office, Prediction
from .serializers import (
    AdmissionSerializer,
    CallTranscriptSerializer,
    EmployeeSerializer,
    FollowUpSerializer,
    LeadActivitySerializer,
    LeadSerializer,
    MeetingSerializer,
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


    @action(detail=False, methods=["post"], url_path="predict-all")
    def predict_all(self, request):
        """Predict every active lead visible to the logged-in user in one request."""
        employee = current_employee(request)
        if employee.role not in [Employee.ADMIN, Employee.MANAGER, Employee.COUNSELLOR]:
            return Response({"detail": "Prediction is not available for this role."}, status=403)

        leads = self.get_queryset().exclude(status__in=["ENROLLED", "LOST"])
        predicted = 0
        failed = []
        for lead in leads:
            try:
                result = predict_lead(lead)
                Prediction.objects.create(
                    lead=lead,
                    admission_probability=result["probability"],
                    priority=result["priority"],
                    expected_revenue=result["expected_revenue"],
                    model_version=result["model_version"],
                )
                predicted += 1
            except Exception as exc:
                failed.append({"lead_id": lead.id, "error": str(exc)})

        return Response({
            "total_eligible": leads.count(),
            "predicted": predicted,
            "failed": len(failed),
            "failed_leads": failed[:10],
            "run_at": timezone.now(),
        })


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


def _lead_accessible(employee, lead):
    if employee.role == Employee.ADMIN:
        return True
    if employee.role == Employee.MANAGER:
        return lead.office_id == employee.office_id
    return lead.assigned_counsellor_id == employee.id


class CallTranscriptViewSet(viewsets.ModelViewSet):
    serializer_class = CallTranscriptSerializer

    def get_queryset(self):
        employee = current_employee(self.request)
        qs = CallTranscript.objects.select_related("lead", "counsellor__user", "lead__office").order_by("-created_at")
        lead_id = self.request.query_params.get("lead")
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        if employee.role == Employee.ADMIN:
            return qs
        if employee.role == Employee.MANAGER:
            return qs.filter(lead__office=employee.office)
        return qs.filter(counsellor=employee)

    def perform_create(self, serializer):
        employee = current_employee(self.request)
        if employee.role != Employee.COUNSELLOR:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only counsellors can save call transcripts.")
        lead = serializer.validated_data["lead"]
        if lead.assigned_counsellor_id != employee.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This lead is not assigned to you.")
        transcript = serializer.save(counsellor=employee, ended_at=timezone.now())
        LeadActivity.objects.create(
            lead=lead, employee=employee, activity_type="CALL",
            remark=f"Call transcript saved: {transcript.transcript[:180]}",
        )


def _send_meeting_invitation(meeting):
    lead = meeting.lead
    if not lead.email:
        return False
    start = meeting.scheduled_at
    end = start + timedelta(minutes=meeting.duration_minutes)
    stamp = lambda dt: dt.astimezone(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ics = "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//EduLead CRM//EN",
        "BEGIN:VEVENT", f"UID:edulead-meeting-{meeting.id}@edulead",
        f"DTSTAMP:{stamp(timezone.now())}", f"DTSTART:{stamp(start)}", f"DTEND:{stamp(end)}",
        f"SUMMARY:EduLead counselling meeting - {lead.student_name}",
        f"DESCRIPTION:Join virtual counselling meeting: {meeting.meeting_url}",
        f"LOCATION:{meeting.meeting_url}", "END:VEVENT", "END:VCALENDAR", ""
    ])
    subject = f"EduLead counselling meeting - {start.astimezone().strftime('%d %b %Y, %I:%M %p')}"
    body = (
        f"Hello {lead.student_name},\n\nYour counselling meeting has been scheduled for "
        f"{start.astimezone().strftime('%d %b %Y at %I:%M %p')}.\n"
        f"Join meeting: {meeting.meeting_url}\n\n{meeting.note}\n\nEduLead CRM"
    )
    msg = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [lead.email])
    msg.attach("edulead-meeting.ics", ics, "text/calendar")
    msg.send(fail_silently=False)
    return True

class MeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingSerializer

    def get_queryset(self):
        employee = current_employee(self.request)
        qs = Meeting.objects.select_related("lead", "counsellor__user", "lead__office").order_by("-scheduled_at")
        lead_id = self.request.query_params.get("lead")
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        if employee.role == Employee.ADMIN:
            return qs
        if employee.role == Employee.MANAGER:
            return qs.filter(lead__office=employee.office)
        return qs.filter(counsellor=employee)

    def perform_create(self, serializer):
        employee = current_employee(self.request)
        if employee.role != Employee.COUNSELLOR:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only counsellors can schedule meetings.")
        lead = serializer.validated_data["lead"]
        if lead.assigned_counsellor_id != employee.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This lead is not assigned to you.")
        meeting_url = f"https://meet.jit.si/EduLead-{lead.id}-{uuid.uuid4().hex[:12]}"
        meeting = serializer.save(counsellor=employee, meeting_url=meeting_url)
        sent = False
        try:
            sent = _send_meeting_invitation(meeting)
        except Exception:
            sent = False
        meeting.invitation_sent = sent
        meeting.save(update_fields=["invitation_sent"])
        LeadActivity.objects.create(
            lead=lead, employee=employee, activity_type="REMARK",
            remark=f"Virtual meeting scheduled for {meeting.scheduled_at}. Invitation {'sent' if sent else 'not sent'}."
        )


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
