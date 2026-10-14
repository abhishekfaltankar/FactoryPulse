import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

from config import (
    DATASET_CSV_PATH, MODEL_ARTIFACT_PATH,
    METADATA_ARTIFACT_PATH, ARTIFACTS_DIR
)
from data.dataset_generator import ensure_dataset_exists
from ml.features import engineer_features, FEATURE_NAMES

def train_predictive_maintenance_model(
    csv_path: Path = DATASET_CSV_PATH,
    n_estimators: int = 150,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Trains a real dual-head machine failure prediction model:
    1. Binary Failure Classifier (predicts machine failure probability)
    2. Multi-Class Failure Mode Classifier (predicts specific mode: TWF, HDF, PWF, OSF, RNF)
    Evaluates real metrics and saves artifacts to disk.
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        ensure_dataset_exists(csv_path)

    df = pd.read_csv(csv_path)

    # Prepare features and targets
    X_df = engineer_features(df)
    X = X_df.to_numpy(dtype=np.float64)
    y_binary = np.array(df["Machine failure"].values, dtype=int)
    y_multiclass = np.array(df["Failure Type"].values, dtype=str)

    # Train / Test split
    X_train, X_test, y_bin_train, y_bin_test, y_mc_train, y_mc_test = train_test_split(
        X, y_binary, y_multiclass, test_size=0.20, random_state=random_state, stratify=y_binary
    )

    # 1. Train Binary Classifier
    binary_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=12,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    binary_model.fit(X_train, y_bin_train)

    # 2. Train Multi-Class Failure Mode Classifier
    # Only train on failed rows + sample of normal rows to specialize in failure mode distinction
    mc_model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=14,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1
    )
    mc_model.fit(X_train, y_mc_train)

    # Evaluation on Test set
    y_bin_pred = binary_model.predict(X_test)
    y_bin_proba = binary_model.predict_proba(X_test)[:, 1]

    accuracy = float(accuracy_score(y_bin_test, y_bin_pred))
    precision = float(precision_score(y_bin_test, y_bin_pred, zero_division=0))
    recall = float(recall_score(y_bin_test, y_bin_pred, zero_division=0))
    f1 = float(f1_score(y_bin_test, y_bin_pred, zero_division=0))
    try:
        roc_auc = float(roc_auc_score(y_bin_test, y_bin_proba))
    except Exception:
        roc_auc = 0.5

    cm = confusion_matrix(y_bin_test, y_bin_pred).tolist()

    # Multi-class evaluation
    y_mc_pred = mc_model.predict(X_test)
    mc_report = classification_report(y_mc_test, y_mc_pred, output_dict=True, zero_division=0)

    # Feature importances
    feature_importances = {
        name: float(round(imp, 4))
        for name, imp in zip(FEATURE_NAMES, binary_model.feature_importances_)
    }
    # Sort descending
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    artifacts_payload = {
        "binary_model": binary_model,
        "multiclass_model": mc_model,
        "feature_names": FEATURE_NAMES
    }

    joblib.dump(artifacts_payload, MODEL_ARTIFACT_PATH)

    metadata = {
        "model_version": "v1.2.0-rf-physics",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "confusion_matrix": cm
        },
        "multiclass_metrics": mc_report,
        "feature_importances": sorted_importances,
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": 12,
            "class_weight": "balanced",
            "random_state": random_state
        }
    }

    with open(METADATA_ARTIFACT_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Model successfully trained and saved to {MODEL_ARTIFACT_PATH}.")
    print(f"Metrics: Accuracy={accuracy:.4f}, Recall={recall:.4f}, Precision={precision:.4f}, F1={f1:.4f}, ROC-AUC={roc_auc:.4f}")
    return metadata

if __name__ == "__main__":
    train_predictive_maintenance_model()
