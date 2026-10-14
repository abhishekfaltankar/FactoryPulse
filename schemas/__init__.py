from schemas.machine import MachineCreate, MachineResponse, MachineUpdate
from schemas.telemetry import TelemetryCreate, TelemetryResponse, TelemetryBatchCreate
from schemas.prediction import PredictionRequest, PredictionResponse, BatchPredictionResponse
from schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from schemas.maintenance import MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate
from schemas.analytics import FleetOverviewResponse, MachineAnalyticsResponse

__all__ = [
    "MachineCreate", "MachineResponse", "MachineUpdate",
    "TelemetryCreate", "TelemetryResponse", "TelemetryBatchCreate",
    "PredictionRequest", "PredictionResponse", "BatchPredictionResponse",
    "AlertCreate", "AlertResponse", "AlertUpdate",
    "MaintenanceCreate", "MaintenanceResponse", "MaintenanceUpdate",
    "FleetOverviewResponse", "MachineAnalyticsResponse"
]
