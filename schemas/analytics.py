from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Any

class FleetOverviewResponse(BaseModel):
    total_machines: int
    operational_count: int
    warning_count: int
    critical_count: int
    maintenance_count: int
    average_health_score: float
    active_alerts_count: int
    total_predictions_today: int
    predicted_failures_count: int
    status_distribution: Dict[str, int]
    failure_mode_distribution: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)

class MachineAnalyticsResponse(BaseModel):
    machine_id: str
    health_score: float
    current_status: str
    telemetry_count: int
    latest_readings: Dict[str, Any]
    recent_predictions: List[Dict[str, Any]]
    active_alerts: List[Dict[str, Any]]
    maintenance_history: List[Dict[str, Any]]
