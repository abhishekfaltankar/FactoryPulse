from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.alert import Alert
from schemas.alert import AlertCreate, AlertResponse, AlertUpdate

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    status_filter: Optional[str] = Query(None, alias="status", description="ACTIVE, ACKNOWLEDGED, or RESOLVED"),
    severity: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, or CRITICAL"),
    machine_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve filtered industrial alerts."""
    query = db.query(Alert)
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if machine_id:
        query = query.filter(Alert.machine_id == machine_id)

    alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
    return alerts

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    """Create a new industrial alert."""
    alert = Alert(
        machine_id=payload.machine_id,
        severity=payload.severity.upper(),
        message=payload.message,
        status="ACTIVE",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an active alert by an operator."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found."
        )
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert

@router.put("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as resolved after corrective action."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found."
        )
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert
