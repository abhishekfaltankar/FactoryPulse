from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from database import get_db
from models.machine import Machine
from models.telemetry import Telemetry
from models.prediction import Prediction
from models.alert import Alert
from models.maintenance import MaintenanceRecord
from schemas.analytics import FleetOverviewResponse, MachineAnalyticsResponse

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview", response_model=FleetOverviewResponse)
def get_fleet_overview(db: Session = Depends(get_db)):
    """Fleet-wide health, status distribution, and failure mode statistics."""
    machines = db.query(Machine).all()
    total_machines = len(machines)

    operational = sum(1 for m in machines if m.status == "OPERATIONAL")
    warning = sum(1 for m in machines if m.status == "WARNING")
    critical = sum(1 for m in machines if m.status == "CRITICAL")
    maintenance = sum(1 for m in machines if m.status == "UNDER_MAINTENANCE")

    avg_health = (sum(m.health_score for m in machines) / total_machines) if total_machines > 0 else 100.0

    active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").count()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total_preds_today = db.query(Prediction).filter(Prediction.timestamp >= today_start).count()
    predicted_failures_today = (
        db.query(Prediction)
        .filter(Prediction.timestamp >= today_start, Prediction.failure_predicted == 1)
        .count()
    )

    # Status distribution
    status_dist = {
        "OPERATIONAL": operational,
        "WARNING": warning,
        "CRITICAL": critical,
        "UNDER_MAINTENANCE": maintenance
    }

    # Failure mode distribution across all historical predictions
    fm_counts = (
        db.query(Prediction.failure_mode, func.count(Prediction.id))
        .group_by(Prediction.failure_mode)
        .all()
    )
    failure_mode_dist = {mode: count for mode, count in fm_counts if mode != "No Failure"}
    if not failure_mode_dist:
        failure_mode_dist = {
            "Power Failure": 0,
            "Tool Wear Failure": 0,
            "Heat Dissipation Failure": 0,
            "Overstrain Failure": 0
        }

    return FleetOverviewResponse(
        total_machines=total_machines,
        operational_count=operational,
        warning_count=warning,
        critical_count=critical,
        maintenance_count=maintenance,
        average_health_score=round(avg_health, 1),
        active_alerts_count=active_alerts,
        total_predictions_today=total_preds_today,
        predicted_failures_count=predicted_failures_today,
        status_distribution=status_dist,
        failure_mode_distribution=failure_mode_dist
    )

@router.get("/machine/{machine_id}", response_model=MachineAnalyticsResponse)
def get_machine_analytics(machine_id: str, db: Session = Depends(get_db)):
    """Deep-dive analytics and historical summary for a specific machine."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine '{machine_id}' not found."
        )

    telemetry_count = db.query(Telemetry).filter(Telemetry.machine_id == machine_id).count()

    latest_reading = (
        db.query(Telemetry)
        .filter(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.timestamp.desc())
        .first()
    )
    latest_dict = {
        "air_temperature": latest_reading.air_temperature,
        "process_temperature": latest_reading.process_temperature,
        "rotational_speed": latest_reading.rotational_speed,
        "torque": latest_reading.torque,
        "tool_wear": latest_reading.tool_wear,
        "timestamp": latest_reading.timestamp.isoformat()
    } if latest_reading else {}

    recent_preds = (
        db.query(Prediction)
        .filter(Prediction.machine_id == machine_id)
        .order_by(Prediction.timestamp.desc())
        .limit(10)
        .all()
    )
    preds_list = [
        {
            "id": p.id,
            "timestamp": p.timestamp.isoformat(),
            "failure_predicted": p.failure_predicted,
            "failure_probability": p.failure_probability,
            "failure_mode": p.failure_mode,
            "confidence_score": p.confidence_score
        } for p in recent_preds
    ]

    active_alerts = (
        db.query(Alert)
        .filter(Alert.machine_id == machine_id, Alert.status == "ACTIVE")
        .all()
    )
    alerts_list = [
        {
            "id": a.id,
            "severity": a.severity,
            "message": a.message,
            "timestamp": a.timestamp.isoformat()
        } for a in active_alerts
    ]

    maintenance_logs = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.machine_id == machine_id)
        .order_by(MaintenanceRecord.scheduled_date.desc())
        .limit(5)
        .all()
    )
    maint_list = [
        {
            "id": m.id,
            "status": m.status,
            "technician": m.technician,
            "notes": m.notes,
            "scheduled_date": m.scheduled_date.isoformat(),
            "cost": m.cost
        } for m in maintenance_logs
    ]

    return MachineAnalyticsResponse(
        machine_id=machine.id,
        health_score=machine.health_score,
        current_status=machine.status,
        telemetry_count=telemetry_count,
        latest_readings=latest_dict,
        recent_predictions=preds_list,
        active_alerts=alerts_list,
        maintenance_history=maint_list
    )
