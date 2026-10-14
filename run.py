#!/usr/bin/env python3
"""
FactoryPulse - Industrial Predictive Maintenance Platform
Main Reproducible Entrypoint and Service Orchestrator
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import init_db
from data.seed import seed_database
from ml.trainer import train_predictive_maintenance_model
from config import MODEL_ARTIFACT_PATH

BANNER = r"""
========================================================================
  ______          _                   _____       _             
 |  ____|        | |                 |  __ \     | |            
 | |__ __ _  ___ | |_ ___  _ __ _   _| |__) |   _| |___  ___    
 |  __/ _` |/ __|| __/ _ \| '__| | | |  ___/ | | | / __|/ _ \   
 | | | (_| | (__ | || (_) | |  | |_| | |   | |_| | \__ \  __/   
 |_|  \__,_|\___| \__\___/|_|   \__, |_|    \__,_|_|___/\___|   
                                 __/ |                          
                                |___/                           
 Industrial Predictive Maintenance & IIoT Machine Telemetry Platform
========================================================================
"""

def startup_pipeline(force_retrain: bool = False):
    print(BANNER)
    print(">> Step 1/3: Initializing Database & Seeding Baseline Fleet...")
    init_db()
    seed_database()

    print("\n>> Step 2/3: Verifying Machine Learning Model Artifacts...")
    if force_retrain or not MODEL_ARTIFACT_PATH.exists():
        print("   Training model on AI4I 2020 Predictive Maintenance Dataset...")
        train_predictive_maintenance_model()
    else:
        print(f"   Model artifacts verified at: {MODEL_ARTIFACT_PATH}")

    print("\n>> Step 3/3: Launching FactoryPulse Production Server...")

def main():
    parser = argparse.ArgumentParser(description="FactoryPulse Industrial Telemetry & ML Platform")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable live auto-reload")
    parser.add_argument("--retrain", action="store_true", help="Force model retraining before startup")
    args = parser.parse_args()

    startup_pipeline(force_retrain=args.retrain)

    import uvicorn
    print(f"\n   -> Application Dashboard: http://{args.host}:{args.port}/")
    print(f"   -> Swagger Interactive Docs: http://{args.host}:{args.port}/docs")
    print(f"   -> OpenAPI Specification: http://{args.host}:{args.port}/openapi.json")
    print(f"   -> Health Inspection: http://{args.host}:{args.port}/api/health\n")

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
