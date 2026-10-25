from django.db.models import OuterRef, Subquery, Sum, Count, Q
from ..models import Prediction

def active_prediction_totals(leads):
    """One query for latest prediction of each active lead; compatible with MySQL."""
    latest = Prediction.objects.filter(lead_id=OuterRef("pk")).order_by("-created_at", "-pk")
    active = leads.exclude(status__in=["ENROLLED", "LOST"]).annotate(
        latest_revenue=Subquery(latest.values("expected_revenue")[:1]),
        latest_probability=Subquery(latest.values("admission_probability")[:1]),
        latest_priority=Subquery(latest.values("priority")[:1]),
    )
    totals = active.aggregate(revenue=Sum("latest_revenue"), probability=Sum("latest_probability"))
    priorities = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for row in active.exclude(latest_priority__isnull=True).values("latest_priority").annotate(n=Count("id")):
        priorities[row["latest_priority"]] = row["n"]
    return float(totals["revenue"] or 0), float(totals["probability"] or 0) / 100, priorities
