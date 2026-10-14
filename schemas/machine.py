from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class MachineBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "CNC Milling Center A1"})
    model: str = Field(..., json_schema_extra={"example": "VF-2SS"})
    machine_type: str = Field(..., description="Type: L, M, or H", json_schema_extra={"example": "M"})
    location: str = Field("Sector 1", json_schema_extra={"example": "Sector 1"})
    status: str = Field("OPERATIONAL", json_schema_extra={"example": "OPERATIONAL"})

class MachineCreate(MachineBase):
    id: str = Field(..., json_schema_extra={"example": "M-101"})
    health_score: Optional[float] = Field(100.0, ge=0.0, le=100.0)

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    machine_type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    health_score: Optional[float] = None
    last_maintenance_date: Optional[datetime] = None

class MachineResponse(MachineBase):
    id: str
    installed_at: datetime
    last_maintenance_date: Optional[datetime] = None
    health_score: float

    model_config = ConfigDict(from_attributes=True)
