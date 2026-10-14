from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class MaintenanceBase(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "M-101"})
    scheduled_date: datetime = Field(default_factory=datetime.utcnow)
    technician: str = Field(..., json_schema_extra={"example": "Alex Vance"})
    notes: Optional[str] = Field(None, json_schema_extra={"example": "Replace spindle bearing and inspect lubrication."})
    status: str = Field("SCHEDULED", description="SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED", json_schema_extra={"example": "SCHEDULED"})
    cost: float = Field(0.0, ge=0.0, json_schema_extra={"example": 350.0})

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    status: Optional[str] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    technician: Optional[str] = None
    cost: Optional[float] = None

class MaintenanceResponse(MaintenanceBase):
    id: int
    completed_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
