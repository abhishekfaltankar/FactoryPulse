from api.routers.machines import router as machines_router
from api.routers.telemetry import router as telemetry_router
from api.routers.predictions import router as predictions_router
from api.routers.alerts import router as alerts_router
from api.routers.maintenance import router as maintenance_router
from api.routers.training import router as training_router
from api.routers.analytics import router as analytics_router

__all__ = [
    "machines_router",
    "telemetry_router",
    "predictions_router",
    "alerts_router",
    "maintenance_router",
    "training_router",
    "analytics_router"
]
