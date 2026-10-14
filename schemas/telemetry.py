from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class TelemetryBase(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "M-101"})
    air_temperature: float = Field(..., ge=250.0, le=350.0, description="Air temperature in Kelvin", json_schema_extra={"example": 298.1})
    process_temperature: float = Field(..., ge=250.0, le=360.0, description="Process temperature in Kelvin", json_schema_extra={"example": 308.6})
    rotational_speed: float = Field(..., ge=500.0, le=3500.0, description="Rotational speed in RPM", json_schema_extra={"example": 1551.0})
    torque: float = Field(..., ge=0.0, le=150.0, description="Torque in Nm", json_schema_extra={"example": 42.8})
    tool_wear: float = Field(..., ge=0.0, le=400.0, description="Tool wear time in minutes", json_schema_extra={"example": 0.0})

class TelemetryCreate(TelemetryBase):
    timestamp: Optional[datetime] = None

class TelemetryBatchCreate(BaseModel):
    readings: List[TelemetryCreate]

class TelemetryResponse(TelemetryBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
