"""
EduLead admission model.

For a real consultancy, replace demo_training_data.csv with exported historical leads.
Target column: converted (1 = admission, 0 = not converted).
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "demo_training_data.csv"
MODEL_FILE = BASE_DIR / "admission_model.joblib"

CATEGORICAL = ["source", "country", "course"]
NUMERIC = ["academic_score", "budget", "completed_followups", "activity_count"]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "converted"


def train():
    data = pd.read_csv(DATA_FILE)

    X = data[FEATURES]
    y = data[TARGET]

    preprocessing = ColumnTransformer(
        transformers=[
            ("category", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("number", StandardScaler(), NUMERIC),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    model.fit(X, y)
    joblib.dump(model, MODEL_FILE)
    print(f"Model saved to: {MODEL_FILE}")


if __name__ == "__main__":
    train()
