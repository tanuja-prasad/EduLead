from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Office(models.Model):
    """One consultancy branch, for example Pune or Mumbai."""

    name = models.CharField(max_length=100)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80, blank=True)
    monthly_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city}"


class Employee(models.Model):
    """Extra CRM details for Django's built-in login user."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    COUNSELLOR = "COUNSELLOR"

    ROLE_CHOICES = [
        (ADMIN, "Admin / CEO / CMO"),
        (MANAGER, "Manager"),
        (COUNSELLOR, "Counsellor"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee")
    office = models.ForeignKey(
        Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role}"


class Lead(models.Model):
    """Student admission enquiry."""

    SOURCE_CHOICES = [
        ("INSTAGRAM", "Instagram"),
        ("FACEBOOK", "Facebook"),
        ("GOOGLE", "Google Ads"),
        ("WEBSITE", "Website"),
        ("WALKIN", "Walk-in"),
        ("DIRECT", "Direct"),
        ("REFERRAL", "Referral"),
        ("OTHER", "Other"),
    ]

    STATUS_CHOICES = [
        ("NEW", "New"),
        ("CONTACTED", "Contacted"),
        ("INTERESTED", "Interested"),
        ("COUNSELLING", "Counselling"),
        ("APPLICATION", "Application"),
        ("OFFER", "Offer Received"),
        ("ENROLLED", "Enrolled"),
        ("LOST", "Lost"),
    ]

    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name="leads")
    student_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    country = models.CharField(max_length=80, blank=True)
    course = models.CharField(max_length=120, blank=True)
    academic_score = models.FloatField(default=60)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    assigned_manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_leads",
        limit_choices_to={"role": Employee.MANAGER},
    )
    assigned_counsellor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counsellor_leads",
        limit_choices_to={"role": Employee.COUNSELLOR},
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.student_name


class LeadActivity(models.Model):
    """Every remark/status/contact event becomes one history row."""

    ACTIVITY_CHOICES = [
        ("CREATED", "Created"),
        ("ASSIGNED", "Assigned"),
        ("CALL", "Call"),
        ("WHATSAPP", "WhatsApp"),
        ("EMAIL", "Email"),
        ("REMARK", "Remark"),
        ("STATUS", "Status Changed"),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    remark = models.TextField(blank=True)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class FollowUp(models.Model):
    """Simple counsellor reminder table."""

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="followups")
    counsellor = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="followups")
    followup_at = models.DateTimeField()
    note = models.CharField(max_length=250, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Admission(models.Model):
    """One successful admission. revenue is the business earned from it."""

    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name="admission")
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    university = models.CharField(max_length=150, blank=True)
    admitted_on = models.DateField()


class Prediction(models.Model):
    """Latest ML output can be shown on the lead and used in revenue projection."""

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="predictions")
    admission_probability = models.FloatField()
    priority = models.CharField(max_length=10)
    expected_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    model_version = models.CharField(max_length=30, default="logistic-v1")
    created_at = models.DateTimeField(auto_now_add=True)

class CallTranscript(models.Model):
    """Transcript captured during a counsellor/student call session."""

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="call_transcripts")
    counsellor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="call_transcripts")
    transcript = models.TextField()
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call - {self.lead.student_name} - {self.created_at:%Y-%m-%d %H:%M}"


class Meeting(models.Model):
    """Virtual counselling meeting with an email/calendar invitation."""

    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    STATUS_CHOICES = [(SCHEDULED, "Scheduled"), (COMPLETED, "Completed"), (CANCELLED, "Cancelled")]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="meetings")
    counsellor = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="meetings")
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    meeting_url = models.URLField(max_length=500)
    note = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SCHEDULED)
    invitation_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Meeting - {self.lead.student_name} - {self.scheduled_at}"
