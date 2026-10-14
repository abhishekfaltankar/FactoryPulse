import json
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from config import METADATA_ARTIFACT_PATH
from ml.trainer import train_predictive_maintenance_model
from ml.predictor import PredictiveMaintenanceInferenceEngine

router = APIRouter(prefix="/api/train", tags=["ML Training"])

@router.post("", status_code=status.HTTP_200_OK)
def trigger_training():
    """Trigger model training with the active industrial dataset."""
    try:
        metadata = train_predictive_maintenance_model()
        # Reload predictor singleton instance
        engine = PredictiveMaintenanceInferenceEngine.get_instance()
        engine.load_artifacts()
        return {
            "success": True,
            "message": "Model successfully retrained and artifacts updated.",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}"
        )

@router.get("/metadata", response_model=Dict[str, Any])
def get_model_metadata():
    """Retrieve active model version, evaluation metrics, and feature importances."""
    if not METADATA_ARTIFACT_PATH.exists():
        metadata = train_predictive_maintenance_model()
        return metadata
    
    with open(METADATA_ARTIFACT_PATH, "r") as f:
        metadata = json.load(f)
    return metadata
