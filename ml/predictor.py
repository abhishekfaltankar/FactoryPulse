import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    MODEL_ARTIFACT_PATH, METADATA_ARTIFACT_PATH,
    WARNING_FAILURE_PROBABILITY_THRESHOLD,
    CRITICAL_FAILURE_PROBABILITY_THRESHOLD
)
from ml.features import engineer_features, FEATURE_NAMES
from ml.trainer import train_predictive_maintenance_model

class PredictiveMaintenanceInferenceEngine:
    """
    Production inference engine that loads real trained scikit-learn artifacts
    and performs real-time failure prediction and failure mode classification.
    """
    _instance: Optional["PredictiveMaintenanceInferenceEngine"] = None

    def __init__(self):
        self.binary_model = None
        self.multiclass_model = None
        self.feature_names = FEATURE_NAMES
        self.metadata = {}
        self.load_artifacts()

    @classmethod
    def get_instance(cls) -> "PredictiveMaintenanceInferenceEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_artifacts(self):
        """Loads model artifacts from disk; trains if not yet present."""
        if not MODEL_ARTIFACT_PATH.exists() or not METADATA_ARTIFACT_PATH.exists():
            print("Model artifacts not found on disk. Initiating training...")
            self.metadata = train_predictive_maintenance_model()

        payload = joblib.load(MODEL_ARTIFACT_PATH)
        self.binary_model = payload["binary_model"]
        self.multiclass_model = payload["multiclass_model"]
        self.feature_names = payload.get("feature_names", FEATURE_NAMES)

        with open(METADATA_ARTIFACT_PATH, "r") as f:
            self.metadata = json.load(f)

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs real ML inference on a single machine sensor reading.
        """
        if self.binary_model is None or self.multiclass_model is None:
            self.load_artifacts()

        # Engineer features
        features_df = engineer_features(input_data)
        X = features_df.to_numpy(dtype=np.float64)

        # 1. Binary failure probability
        proba = self.binary_model.predict_proba(X)[0]
        failure_prob = float(proba[1])
        failure_pred = int(self.binary_model.predict(X)[0])

        # 2. Multi-class failure mode prediction
        mc_classes = self.multiclass_model.classes_
        mc_probas = self.multiclass_model.predict_proba(X)[0]
        mc_prob_dict = {str(cls_name): float(p) for cls_name, p in zip(mc_classes, mc_probas)}

        # If binary predicts failure or probability exceeds warning threshold, choose highest failure mode
        if failure_prob >= WARNING_FAILURE_PROBABILITY_THRESHOLD or failure_pred == 1:
            # Exclude 'No Failure' if possible
            failure_modes_only = {k: v for k, v in mc_prob_dict.items() if k != "No Failure"}
            if failure_modes_only:
                predicted_mode = max(failure_modes_only, key=failure_modes_only.get)
            else:
                predicted_mode = str(self.multiclass_model.predict(X)[0])
        else:
            predicted_mode = "No Failure"

        # Determine risk level
        if failure_prob >= CRITICAL_FAILURE_PROBABILITY_THRESHOLD:
            risk_level = "CRITICAL"
        elif failure_prob >= WARNING_FAILURE_PROBABILITY_THRESHOLD:
            risk_level = "WARNING"
        else:
            risk_level = "NORMAL"

        # Confidence score
        confidence = float(max(proba))

        # Top feature values
        features_dict = {
            col: round(float(features_df[col].iloc[0]), 3)
            for col in self.feature_names
        }

        # Calculate impact on health score
        health_penalty = failure_prob * 100.0
        calculated_health_score = max(0.0, min(100.0, round(100.0 - health_penalty, 1)))

        return {
            "failure_predicted": failure_pred,
            "failure_probability": round(failure_prob, 4),
            "failure_mode": predicted_mode,
            "risk_level": risk_level,
            "confidence_score": round(confidence, 4),
            "model_version": self.metadata.get("model_version", "v1.2.0"),
            "health_score_estimate": calculated_health_score,
            "failure_mode_probabilities": {k: round(v, 4) for k, v in mc_prob_dict.items()},
            "features": features_dict
        }

    def batch_predict(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Runs batch inference over a list of sensor reading dicts."""
        if not data_list:
            return []

        if self.binary_model is None or self.multiclass_model is None:
            self.load_artifacts()

        df_in = pd.DataFrame(data_list)
        features_df = engineer_features(df_in)
        X = features_df.to_numpy(dtype=np.float64)

        probas = self.binary_model.predict_proba(X)
        preds = self.binary_model.predict(X)
        mc_classes = self.multiclass_model.classes_
        mc_probas = self.multiclass_model.predict_proba(X)

        results = []
        for i in range(len(data_list)):
            prob_fail = float(probas[i][1])
            is_fail = int(preds[i])

            mc_prob_dict = {str(cls_name): float(p) for cls_name, p in zip(mc_classes, mc_probas[i])}
            if prob_fail >= WARNING_FAILURE_PROBABILITY_THRESHOLD or is_fail == 1:
                failure_modes_only = {k: v for k, v in mc_prob_dict.items() if k != "No Failure"}
                predicted_mode = max(failure_modes_only, key=failure_modes_only.get) if failure_modes_only else "No Failure"
            else:
                predicted_mode = "No Failure"

            if prob_fail >= CRITICAL_FAILURE_PROBABILITY_THRESHOLD:
                risk = "CRITICAL"
            elif prob_fail >= WARNING_FAILURE_PROBABILITY_THRESHOLD:
                risk = "WARNING"
            else:
                risk = "NORMAL"

            results.append({
                "failure_predicted": is_fail,
                "failure_probability": round(prob_fail, 4),
                "failure_mode": predicted_mode,
                "risk_level": risk,
                "confidence_score": round(float(max(probas[i])), 4),
                "model_version": self.metadata.get("model_version", "v1.2.0")
            })

        return results
