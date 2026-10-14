import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import init_db, get_db
from data.seed import seed_database
from ml.predictor import PredictiveMaintenanceInferenceEngine
from api.routers import (
    machines_router,
    telemetry_router,
    predictions_router,
    alerts_router,
    maintenance_router,
    training_router,
    analytics_router
)
from config import FRONTEND_DIR, MODEL_ARTIFACT_PATH

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB, seed default fleet if empty, preload ML model
    init_db()
    seed_database()
    # Preload ML inference engine
    PredictiveMaintenanceInferenceEngine.get_instance()
    yield
    # Shutdown

app = FastAPI(
    title="FactoryPulse - Industrial Predictive Maintenance Platform",
    description="Enterprise Real-Time Machine Telemetry, Physical Anomaly Detection & Predictive Maintenance API",
    version="1.2.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(machines_router)
app.include_router(telemetry_router)
app.include_router(predictions_router)
app.include_router(alerts_router)
app.include_router(maintenance_router)
app.include_router(training_router)
app.include_router(analytics_router)

# Health endpoint
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Backend readiness and dependency health inspection."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    model_status = "loaded" if MODEL_ARTIFACT_PATH.exists() else "not_loaded"

    return {
        "status": "online",
        "service": "FactoryPulse API",
        "version": "1.2.0",
        "database": db_status,
        "ml_model": model_status
    }

# Static files and Frontend Single Page App
if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

@app.get("/", include_in_schema=False)
def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "FactoryPulse API is active. Navigate to /docs for interactive API documentation."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
