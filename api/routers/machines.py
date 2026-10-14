from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.machine import Machine
from schemas.machine import MachineCreate, MachineResponse, MachineUpdate

router = APIRouter(prefix="/api/machines", tags=["Machines"])

@router.get("", response_model=List[MachineResponse])
def get_machines(db: Session = Depends(get_db)):
    """List all machines across the industrial facility."""
    machines = db.query(Machine).all()
    return machines

@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific machine."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{machine_id}' not found."
        )
    return machine

@router.post("", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreate, db: Session = Depends(get_db)):
    """Register a new industrial machine."""
    existing = db.query(Machine).filter(Machine.id == payload.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Machine with ID '{payload.id}' already exists."
        )

    machine = Machine(
        id=payload.id,
        name=payload.name,
        model=payload.model,
        machine_type=payload.machine_type,
        location=payload.location,
        status=payload.status,
        health_score=payload.health_score or 100.0
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine

@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(machine_id: str, payload: MachineUpdate, db: Session = Depends(get_db)):
    """Update machine parameters, status, or health score."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{machine_id}' not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(machine, field, val)

    db.commit()
    db.refresh(machine)
    return machine

@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    """Remove a decommissioned machine."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID '{machine_id}' not found."
        )
    db.delete(machine)
    db.commit()
    return None
