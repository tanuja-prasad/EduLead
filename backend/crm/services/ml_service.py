"""ML logic kept outside views so it is easy to explain and test."""

from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = Path(__file__).resolve().parents[3] / "ml" / "admission_model.joblib"


def lead_features(lead):
    return {
        "source": lead.source,
        "country": lead.country or "Unknown",
        "course": lead.course or "Unknown",
        "academic_score": float(lead.academic_score),
        "budget": float(lead.budget),
        "completed_followups": lead.followups.filter(completed=True).count(),
        "activity_count": lead.activities.count(),
    }


def predict_lead(lead):
    """Return probability, priority and probability-weighted expected revenue."""

    features = lead_features(lead)

    model_loaded = False
    if MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
            frame = pd.DataFrame([features])
            probability = float(model.predict_proba(frame)[0][1]) * 100
            version = "logistic-v1"
            model_loaded = True
        except Exception:
            # A joblib/scikit-learn model can become incompatible after a
            # library upgrade. Keep the demo usable and allow retraining with
            # the backend environment instead of returning HTTP 500.
            model_loaded = False

    if not model_loaded:
        # Demo fallback only. Train the model before real deployment.
        probability = 20
        probability += 0.30 * features["academic_score"]
        probability += min(features["budget"] / 100000, 15)
        probability += features["completed_followups"] * 5
        probability += min(features["activity_count"], 10)
        probability = min(95, max(5, probability))
        version = "demo-fallback"

    if probability >= 70:
        priority = "HIGH"
    elif probability >= 40:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    expected_revenue = float(lead.expected_fee) * probability / 100

    return {
        "probability": round(probability, 2),
        "priority": priority,
        "expected_revenue": round(expected_revenue, 2),
        "model_version": version,
    }
