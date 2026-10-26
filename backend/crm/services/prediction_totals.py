
from collections import defaultdict

from django.db.models import OuterRef, Subquery

from ..models import Prediction


def prediction_summary_by_office(leads):
    """
    Calculate latest active-lead prediction totals once.

    Returns:
        {
            office_id: {
                "revenue": float,
                "admissions": float,
                "priority": {"HIGH": int, "MEDIUM": int, "LOW": int}
            }
        }
    """

    latest_prediction = (
        Prediction.objects
        .filter(lead_id=OuterRef("pk"))
        .order_by("-created_at", "-pk")
    )

    active_leads = (
        leads.exclude(status__in=["ENROLLED", "LOST"])
        .annotate(
            latest_revenue=Subquery(
                latest_prediction.values("expected_revenue")[:1]
            ),
            latest_probability=Subquery(
                latest_prediction.values("admission_probability")[:1]
            ),
            latest_priority=Subquery(
                latest_prediction.values("priority")[:1]
            ),
        )
        .values(
            "office_id",
            "latest_revenue",
            "latest_probability",
            "latest_priority",
        )
    )

    summaries = defaultdict(
        lambda: {
            "revenue": 0.0,
            "admissions": 0.0,
            "priority": {
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
            },
        }
    )

    for lead in active_leads.iterator(chunk_size=1000):
        summary = summaries[lead["office_id"]]

        summary["revenue"] += float(
            lead["latest_revenue"] or 0
        )

        summary["admissions"] += (
            float(lead["latest_probability"] or 0) / 100
        )

        priority = lead["latest_priority"]

        if priority in summary["priority"]:
            summary["priority"][priority] += 1

    return dict(summaries)


def active_prediction_totals(leads):
    """
    Backward-compatible helper for existing dashboard calls.
    """

    summaries = prediction_summary_by_office(leads)

    total_revenue = 0.0
    total_admissions = 0.0
    priorities = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for summary in summaries.values():
        total_revenue += summary["revenue"]
        total_admissions += summary["admissions"]

        for priority in priorities:
            priorities[priority] += summary["priority"][priority]

    return total_revenue, total_admissions, priorities
