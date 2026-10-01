from calendar import month_abbr

from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone

from ..models import Admission, Employee, Lead, Office, Prediction


def money(value):
    return float(value or 0)


def office_performance():
    rows = []

    for office in Office.objects.filter(active=True):
        leads = Lead.objects.filter(office=office)
        total = leads.count()
        admissions = Admission.objects.filter(lead__office=office)
        enrolled = admissions.count()
        revenue = admissions.aggregate(total=Sum("revenue"))["total"] or 0

        latest_predictions = []
        for lead in leads.exclude(status__in=["ENROLLED", "LOST"]):
            prediction = lead.predictions.order_by("-created_at").first()
            if prediction:
                latest_predictions.append(float(prediction.expected_revenue))

        expected_revenue = sum(latest_predictions)

        rows.append({
            "office_id": office.id,
            "office": office.name,
            "city": office.city,
            "leads": total,
            "admissions": enrolled,
            "conversion": round(enrolled * 100 / total, 1) if total else 0,
            "revenue": money(revenue),
            "expected_revenue": round(expected_revenue, 2),
            "monthly_expense": money(office.monthly_expense),
            "projected_profit": round(money(revenue) + expected_revenue - money(office.monthly_expense), 2),
        })

    return rows


def employee_performance(role):
    relation = "managed_leads" if role == Employee.MANAGER else "counsellor_leads"
    rows = []

    for employee in Employee.objects.select_related("user", "office").filter(role=role, active=True):
        leads = getattr(employee, relation).all()
        assigned = leads.count()
        converted = leads.filter(status="ENROLLED").count()
        revenue = Admission.objects.filter(lead__in=leads).aggregate(total=Sum("revenue"))["total"] or 0

        rows.append({
            "id": employee.id,
            "name": employee.user.get_full_name() or employee.user.username,
            "office": employee.office.name if employee.office else "All Offices",
            "assigned": assigned,
            "converted": converted,
            "conversion": round(converted * 100 / assigned, 1) if assigned else 0,
            "revenue": money(revenue),
        })

    return rows


def monthly_revenue():
    year = timezone.localdate().year
    actual = {
        row["month"]: money(row["revenue"])
        for row in Admission.objects.filter(admitted_on__year=year)
        .annotate(month=ExtractMonth("admitted_on"))
        .values("month")
        .annotate(revenue=Sum("revenue"))
    }

    current_month = timezone.localdate().month
    expected_this_month = sum(
        float(p.expected_revenue)
        for p in Prediction.objects.filter(
            lead__status__in=["NEW", "CONTACTED", "INTERESTED", "COUNSELLING", "APPLICATION", "OFFER"]
        ).order_by("lead_id", "-created_at").distinct("lead_id")
    ) if False else 0

    # MySQL does not support DISTINCT ON. Calculate latest prediction in Python.
    latest_expected = 0
    for lead in Lead.objects.exclude(status__in=["ENROLLED", "LOST"]):
        prediction = lead.predictions.order_by("-created_at").first()
        if prediction:
            latest_expected += float(prediction.expected_revenue)

    rows = []
    for month in range(1, 13):
        expected = actual.get(month, 0)
        if month == current_month:
            expected += latest_expected
        rows.append({
            "month": month_abbr[month],
            "actual_revenue": actual.get(month, 0),
            "expected_revenue": round(expected, 2),
        })

    return rows
