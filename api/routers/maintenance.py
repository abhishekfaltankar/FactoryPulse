from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.machine import Machine
from models.maintenance import MaintenanceRecord
from schemas.maintenance import MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])

@router.get("", response_model=List[MaintenanceResponse])
def get_maintenance_records(
    status_filter: Optional[str] = Query(None, alias="status"),
    machine_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve maintenance work orders and logs."""
    query = db.query(MaintenanceRecord)
    if status_filter:
        query = query.filter(MaintenanceRecord.status == status_filter.upper())
    if machine_id:
        query = query.filter(MaintenanceRecord.machine_id == machine_id)

    records = query.order_by(MaintenanceRecord.scheduled_date.desc()).limit(limit).all()
    return records

@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def schedule_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db)):
    """Schedule a new maintenance service order."""
    machine = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{payload.machine_id}' not found."
        )

    record = MaintenanceRecord(
        machine_id=payload.machine_id,
        scheduled_date=payload.scheduled_date or datetime.now(timezone.utc),
        technician=payload.technician,
        notes=payload.notes,
        status=payload.status.upper(),
        cost=payload.cost
    )
    db.add(record)

    # If status is IN_PROGRESS, set machine to UNDER_MAINTENANCE
    if payload.status.upper() == "IN_PROGRESS":
        machine.status = "UNDER_MAINTENANCE"

    db.commit()
    db.refresh(record)
    return record

@router.put("/{record_id}", response_model=MaintenanceResponse)
def update_maintenance_record(record_id: int, payload: MaintenanceUpdate, db: Session = Depends(get_db)):
    """Update maintenance task status, notes, technician, or cost."""
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with ID {record_id} not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if field == "status" and val:
            record.status = val.upper()
            if val.upper() == "COMPLETED":
                record.completed_date = datetime.now(timezone.utc)
                # Reset machine health and status
                machine = db.query(Machine).filter(Machine.id == record.machine_id).first()
                if machine:
                    machine.status = "OPERATIONAL"
                    machine.health_score = 100.0
                    machine.last_maintenance_date = datetime.now(timezone.utc)
        else:
            setattr(record, field, val)

    db.commit()
    db.refresh(record)
    return record

@router.get("/machine/{machine_id}", response_model=List[MaintenanceResponse])
def get_machine_maintenance_history(machine_id: str, db: Session = Depends(get_db)):
    """Get all maintenance logs for a specific machine."""
    records = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.machine_id == machine_id)
        .order_by(MaintenanceRecord.scheduled_date.desc())
        .all()
    )
    return records
