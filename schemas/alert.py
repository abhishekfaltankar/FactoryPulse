from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "M-101"})
    severity: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL", json_schema_extra={"example": "HIGH"})
    message: str = Field(..., json_schema_extra={"example": "High probability of Heat Dissipation Failure detected"})

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    status: str = Field(..., description="ACTIVE, ACKNOWLEDGED, RESOLVED", json_schema_extra={"example": "ACKNOWLEDGED"})

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime
    status: str
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
