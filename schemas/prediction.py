from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class PredictionRequest(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "M-101"})
    machine_type: str = Field("M", description="Type: L, M, or H", json_schema_extra={"example": "M"})
    air_temperature: float = Field(..., ge=250.0, le=350.0, json_schema_extra={"example": 298.2})
    process_temperature: float = Field(..., ge=250.0, le=360.0, json_schema_extra={"example": 308.7})
    rotational_speed: float = Field(..., ge=500.0, le=3500.0, json_schema_extra={"example": 1500.0})
    torque: float = Field(..., ge=0.0, le=150.0, json_schema_extra={"example": 40.0})
    tool_wear: float = Field(..., ge=0.0, le=400.0, json_schema_extra={"example": 15.0})

class PredictionResponse(BaseModel):
    id: Optional[int] = None
    machine_id: str
    timestamp: datetime
    failure_predicted: int = Field(..., description="1 if failure is predicted, 0 otherwise")
    failure_probability: float = Field(..., description="Estimated probability of failure")
    failure_mode: str = Field(..., description="Predicted failure mode or 'No Failure'")
    risk_level: str = Field(..., description="NORMAL, WARNING, or CRITICAL")
    confidence_score: float
    model_version: str
    features: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class BatchPredictionResponse(BaseModel):
    count: int
    predictions: List[PredictionResponse]
