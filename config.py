import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ML_DIR = BASE_DIR / "ml"
ARTIFACTS_DIR = ML_DIR / "artifacts"
FRONTEND_DIR = BASE_DIR / "frontend"

for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, ML_DIR, ARTIFACTS_DIR, FRONTEND_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/factorypulse.db")

MODEL_ARTIFACT_PATH = ARTIFACTS_DIR / "predictive_maintenance_model.joblib"
METADATA_ARTIFACT_PATH = ARTIFACTS_DIR / "model_metadata.json"
DATASET_CSV_PATH = RAW_DATA_DIR / "ai4i2020.csv"

# Prediction thresholds
WARNING_FAILURE_PROBABILITY_THRESHOLD = 0.40
CRITICAL_FAILURE_PROBABILITY_THRESHOLD = 0.70
