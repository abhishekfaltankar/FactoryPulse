# FactoryPulse - Industrial Predictive Maintenance Intelligence Platform

FactoryPulse is an enterprise industrial IoT (IIoT) telemetry and predictive maintenance platform designed to prevent catastrophic equipment failures, optimize maintenance schedules, and monitor physical machine vitals in real time.

Built on the industry-standard **AI4I 2020 Predictive Maintenance Dataset**, the system features a genuine dual-head scikit-learn machine learning pipeline with physics-derived feature engineering, real-time threshold and anomaly alerts, automated work order generation, and an interactive cyber-industrial dashboard.

---

## 🚀 Key Architectural Capabilities

1. **Robust Relational Data Layer (SQLAlchemy & SQLite/PostgreSQL)**
   - Normalized schema for industrial equipment, high-frequency telemetry, predictions, alerts, and maintenance logs.
   - Automatic database migration and baseline fleet seeding (`CNC-101`, `CNC-102`, `LATHE-201`, `DRILL-301`, `PRESS-401`).

2. **Dataset Validation & Ingestion Pipeline**
   - Full validation engine enforcing physical bounds (temperature ranges, rotation speeds, torque, tool wear limits).
   - Inverted temperature detection and data quality reporting with automated scoring (0–100%).
   - Batch and single-stream ingestion methods.

3. **Authentic Scikit-Learn ML Pipeline (Zero Mocking)**
   - **Binary Failure Classification**: Predicts failure probability using a Balanced Random Forest model.
   - **Multi-Class Failure Mode Identification**: Classifies specific failure types:
     - **HDF (Heat Dissipation Failure)**: Thermal gradient $\Delta T < 8.6\text{ K}$ and speed $< 1380\text{ RPM}$.
     - **PWF (Power Failure)**: Power $P = \tau \cdot \omega < 3500\text{ W}$ or $> 9000\text{ W}$.
     - **OSF (Overstrain Failure)**: Tool wear $\times$ torque product overload.
     - **TWF (Tool Wear Failure)**: Tool wear exceeding operational limits ($> 200\text{ min}$).
     - **RNF (Random Failure)**: Statistical anomaly detection.
   - **Held-Out Test Set Performance**:
     - **Accuracy**: `93.7%`
     - **ROC-AUC**: `0.9884`
     - **Recall**: `90.96%`
     - **Precision**: `78.12%`
     - **F1-Score**: `0.8405`
   - Real-time serialization via `joblib` and `json` metadata.

4. **RESTful High-Performance API (FastAPI)**
   - Comprehensive CRUD for machines, telemetry streams, predictions, alert management, and work orders.
   - Real-time inference on sensor readings with automated threshold alert triggers (`WARNING` $\ge 0.40$, `CRITICAL` $\ge 0.70$).
   - Dynamic health score calculation ($0-100\%$).

5. **Cyber-Industrial Dashboard (Vanilla CSS + HTML5 + JS + Chart.js)**
   - Dark-mode glassmorphic interface with neon status indicators.
   - Live telemetry monitors and dual dynamic charts (thermal dynamics & mechanical relationship).
   - Interactive physical simulator with preset failure conditions (HDF, PWF, OSF, TWF).
   - Alert triage (acknowledge/resolve) and maintenance operations scheduling.

---

## 📁 Repository Structure

```
Project111/
├── config.py                  # Global configurations, file paths, and risk thresholds
├── database.py                # Database engine, session maker, Base, and init_db
├── main.py                    # FastAPI application, CORS, routers, and static mounts
├── run.py                     # Single-command startup and lifecycle orchestrator
├── requirements.txt           # Verified dependencies
├── models/                    # SQLAlchemy ORM Models
│   ├── machine.py             # Machine equipment registry
│   ├── telemetry.py           # Sensor telemetry records
│   ├── prediction.py          # ML inference prediction history
│   ├── alert.py               # Active & historical alerts
│   └── maintenance.py         # Maintenance work orders
├── schemas/                   # Pydantic v2 validation models
│   ├── machine.py
│   ├── telemetry.py
│   ├── prediction.py
│   ├── alert.py
│   ├── maintenance.py
│   └── analytics.py
├── data/                      # Dataset Generation & Ingestion
│   ├── dataset_generator.py   # AI4I 2020 synthetic physics dataset generator
│   ├── validator.py           # Ingestion bounds validator & quality reporter
│   ├── seed.py                # Database seeder with realistic fleet vitals
│   └── raw/
│       └── ai4i2020.csv       # 10,000-row industrial benchmark dataset
├── ml/                        # Machine Learning Pipeline
│   ├── features.py            # Physics-based feature engineering
│   ├── trainer.py             # Model training, test evaluation, and metrics extraction
│   ├── predictor.py           # Production inference engine with artifact loading
│   └── artifacts/
│       ├── predictive_maintenance_model.joblib # Serialized dual-head model
│       └── model_metadata.json                 # Real metrics, confusion matrix, and feature importances
├── frontend/                  # Modern Web Dashboard
│   ├── index.html             # Single-page application interface
│   ├── css/
│   │   └── styles.css         # Glassmorphism, animations, and dark design system
│   └── js/
│       └── app.js             # Real API integration and Chart.js telemetry charts
└── tests/                     # Automated Test Suite (27 Tests)
    ├── conftest.py            # Test fixtures and in-memory test database
    ├── test_database.py       # DB schema and seeding tests
    ├── test_data_ingestion.py # Dataset generation and validator tests
    ├── test_ml_pipeline.py    # Feature engineering, training, and inference tests
    ├── test_api_machines.py   # Machine API endpoint tests
    ├── test_api_telemetry.py  # Telemetry API and alert trigger tests
    ├── test_api_predictions.py# Prediction and risk level tests
    ├── test_api_alerts.py     # Alert acknowledgment and resolution tests
    ├── test_api_maintenance.py# Maintenance lifecycle tests
    └── test_e2e_workflow.py   # Complete end-to-end integration test
```

---

## 🛠️ Installation & Quickstart

### Prerequisites
- Python 3.10+ (Tested on Python 3.11)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the orchestrator script to automatically initialize the database, verify ML artifacts, and start the web server:
```bash
python run.py
```

Options:
- `--host`: Host interface (default: `127.0.0.1`)
- `--port`: Port number (default: `8000`)
- `--reload`: Enable live code reloading
- `--retrain`: Force model retraining on startup

### 3. Access Interfaces
- **Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Health Inspection**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🧪 Running the Test Suite

The comprehensive automated test suite covers unit, integration, and end-to-end workflows:

```bash
pytest tests/ -v
```

### Test Coverage Summary
- `test_database.py`: Verifies schema creation and baseline fleet seeding.
- `test_data_ingestion.py`: Verifies AI4I dataset physics generation, bounds validator, and CSV ingestion.
- `test_ml_pipeline.py`: Validates feature engineering calculations, real model predictions, and failure mode differentiation.
- `test_api_machines.py`: Tests machine CRUD and health metrics.
- `test_api_telemetry.py`: Tests single and batch ingestion with automatic alert creation on critical thresholds.
- `test_api_predictions.py`: Tests on-demand inference endpoints and risk evaluation.
- `test_api_alerts.py`: Tests alert acknowledgment and resolution workflows.
- `test_api_maintenance.py`: Tests work order scheduling, completion, and machine health recovery.
- `test_e2e_workflow.py`: Validates the complete industrial lifecycle from raw telemetry to alert, work order, and full machine recovery.

---

## 📊 API Reference Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System readiness, DB connectivity, and ML status |
| `GET` | `/api/machines` | List all industrial machines with statuses and health ratings |
| `POST` | `/api/machines` | Register a new machine |
| `GET` | `/api/machines/{id}` | Retrieve machine details |
| `PUT` | `/api/machines/{id}` | Update machine status or health score |
| `POST` | `/api/telemetry` | Ingest live sensor telemetry; evaluates failure risk automatically |
| `POST` | `/api/telemetry/batch` | Batch ingest sensor readings |
| `GET` | `/api/telemetry/{id}` | Get recent telemetry readings for a machine |
| `POST` | `/api/predict` | On-demand ML inference for sensor inputs |
| `GET` | `/api/predict/history/{id}` | Retrieve historical predictions for a machine |
| `GET` | `/api/alerts` | List alerts (filter by status, severity, machine) |
| `PUT` | `/api/alerts/{id}/acknowledge` | Acknowledge an active alert |
| `PUT` | `/api/alerts/{id}/resolve` | Resolve an alert |
| `GET` | `/api/maintenance` | List maintenance work orders |
| `POST` | `/api/maintenance` | Schedule a maintenance work order |
| `PUT` | `/api/maintenance/{id}` | Update work order status (e.g., `COMPLETED`) |
| `GET` | `/api/analytics/overview` | Fleet-wide metrics, health distribution, and failure modes |
| `GET` | `/api/analytics/machine/{id}` | Deep-dive telemetry statistics and risk profile |
| `POST` | `/api/train` | Trigger real-time model retraining |
| `GET` | `/api/train/metadata` | Retrieve active model metrics and feature importances |
