from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.machine import Machine
from models.prediction import Prediction
from models.alert import Alert
from schemas.prediction import PredictionRequest, PredictionResponse
from ml.predictor import PredictiveMaintenanceInferenceEngine

router = APIRouter(prefix="/api/predict", tags=["Predictions"])

@router.post("", response_model=PredictionResponse)
def run_prediction(payload: PredictionRequest, db: Session = Depends(get_db)):
    """
    On-demand real ML inference endpoint. Evaluates sensor parameters,
    predicts failure probability, identifies failure modes, persists prediction,
    and returns comprehensive diagnostics.
    """
    engine = PredictiveMaintenanceInferenceEngine.get_instance()
    pred_res = engine.predict(payload.model_dump())

    now = datetime.now(timezone.utc)
    pred_record = Prediction(
        machine_id=payload.machine_id,
        timestamp=now,
        failure_predicted=pred_res["failure_predicted"],
        failure_probability=pred_res["failure_probability"],
        failure_mode=pred_res["failure_mode"],
        confidence_score=pred_res["confidence_score"],
        model_version=pred_res["model_version"],
        features=json.dumps(pred_res["features"])
    )
    db.add(pred_record)

    # If machine exists, update health score
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if machine:
        machine.health_score = pred_res["health_score_estimate"]
        if pred_res["risk_level"] == "CRITICAL":
            machine.status = "CRITICAL"
            db.add(Alert(
                machine_id=payload.machine_id,
                timestamp=now,
                severity="CRITICAL",
                message=f"CRITICAL risk ({pred_res['failure_probability']*100:.1f}%) of {pred_res['failure_mode']} in predictive check.",
                status="ACTIVE"
            ))
        elif pred_res["risk_level"] == "WARNING":
            if machine.status != "CRITICAL":
                machine.status = "WARNING"
            db.add(Alert(
                machine_id=payload.machine_id,
                timestamp=now,
                severity="HIGH",
                message=f"WARNING: Elevated risk ({pred_res['failure_probability']*100:.1f}%) of {pred_res['failure_mode']}.",
                status="ACTIVE"
            ))

    db.commit()
    db.refresh(pred_record)

    return PredictionResponse(
        id=pred_record.id,
        machine_id=payload.machine_id,
        timestamp=now,
        failure_predicted=pred_res["failure_predicted"],
        failure_probability=pred_res["failure_probability"],
        failure_mode=pred_res["failure_mode"],
        risk_level=pred_res["risk_level"],
        confidence_score=pred_res["confidence_score"],
        model_version=pred_res["model_version"],
        features=pred_res["features"]
    )

@router.get("/history/{machine_id}", response_model=List[PredictionResponse])
def get_prediction_history(
    machine_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve historical ML predictions for a machine."""
    preds = (
        db.query(Prediction)
        .filter(Prediction.machine_id == machine_id)
        .order_by(Prediction.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    results = []
    for p in preds:
        risk = "NORMAL"
        if p.failure_probability >= 0.70:
            risk = "CRITICAL"
        elif p.failure_probability >= 0.40:
            risk = "WARNING"

        feats = json.loads(p.features) if p.features else {}
        results.append(PredictionResponse(
            id=p.id,
            machine_id=p.machine_id,
            timestamp=p.timestamp,
            failure_predicted=p.failure_predicted,
            failure_probability=p.failure_probability,
            failure_mode=p.failure_mode,
            risk_level=risk,
            confidence_score=p.confidence_score,
            model_version=p.model_version,
            features=feats
        ))
    return results
