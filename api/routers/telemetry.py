from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.machine import Machine
from models.telemetry import Telemetry
from models.prediction import Prediction
from models.alert import Alert
from schemas.telemetry import TelemetryCreate, TelemetryResponse, TelemetryBatchCreate
from ml.predictor import PredictiveMaintenanceInferenceEngine

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """
    Ingests live sensor telemetry, runs real-time ML inference,
    updates machine health, and auto-generates alerts if abnormal risk is detected.
    """
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{payload.machine_id}' does not exist."
        )

    now = payload.timestamp or datetime.now(timezone.utc)
    reading = Telemetry(
        machine_id=payload.machine_id,
        timestamp=now,
        air_temperature=payload.air_temperature,
        process_temperature=payload.process_temperature,
        rotational_speed=payload.rotational_speed,
        torque=payload.torque,
        tool_wear=payload.tool_wear
    )
    db.add(reading)

    # Run real ML inference
    engine = PredictiveMaintenanceInferenceEngine.get_instance()
    inference_input = {
        "machine_id": payload.machine_id,
        "machine_type": machine.machine_type,
        "air_temperature": payload.air_temperature,
        "process_temperature": payload.process_temperature,
        "rotational_speed": payload.rotational_speed,
        "torque": payload.torque,
        "tool_wear": payload.tool_wear
    }
    pred_res = engine.predict(inference_input)

    # Record prediction
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

    # Update machine health score
    machine.health_score = pred_res["health_score_estimate"]

    # Trigger alerts if failure risk is elevated
    if pred_res["risk_level"] == "CRITICAL":
        machine.status = "CRITICAL"
        alert = Alert(
            machine_id=payload.machine_id,
            timestamp=now,
            severity="CRITICAL",
            message=f"CRITICAL risk ({pred_res['failure_probability']*100:.1f}%) of {pred_res['failure_mode']}. Immediate inspection required.",
            status="ACTIVE"
        )
        db.add(alert)
    elif pred_res["risk_level"] == "WARNING":
        if machine.status != "CRITICAL":
            machine.status = "WARNING"
        alert = Alert(
            machine_id=payload.machine_id,
            timestamp=now,
            severity="HIGH",
            message=f"Elevated risk ({pred_res['failure_probability']*100:.1f}%) of {pred_res['failure_mode']}.",
            status="ACTIVE"
        )
        db.add(alert)
    else:
        if machine.status not in ["UNDER_MAINTENANCE"]:
            machine.status = "OPERATIONAL"

    db.commit()
    db.refresh(reading)
    return reading

@router.post("/batch", status_code=status.HTTP_201_CREATED)
def ingest_batch_telemetry(payload: TelemetryBatchCreate, db: Session = Depends(get_db)):
    """Ingest a batch of telemetry sensor readings."""
    if not payload.readings:
        return {"ingested_count": 0}

    now = datetime.now(timezone.utc)
    records = []
    for item in payload.readings:
        records.append(Telemetry(
            machine_id=item.machine_id,
            timestamp=item.timestamp or now,
            air_temperature=item.air_temperature,
            process_temperature=item.process_temperature,
            rotational_speed=item.rotational_speed,
            torque=item.torque,
            tool_wear=item.tool_wear
        ))

    db.bulk_save_objects(records)
    db.commit()
    return {"ingested_count": len(records), "message": f"Successfully ingested {len(records)} readings."}

@router.get("/{machine_id}", response_model=List[TelemetryResponse])
def get_machine_telemetry(
    machine_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve the latest telemetry readings for a specific machine."""
    readings = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return readings
