import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.telemetry import Telemetry
from data.dataset_generator import generate_ai4i2020_dataset
from data.validator import DatasetValidator

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_generate_ai4i2020_dataset():
    df = generate_ai4i2020_dataset(n_samples=200, seed=42)
    assert len(df) == 200
    assert "Air temperature [K]" in df.columns
    assert "Process temperature [K]" in df.columns
    assert "Machine failure" in df.columns
    assert "Failure Type" in df.columns
    assert set(df["Type"].unique()).issubset({"L", "M", "H"})

def test_dataset_validator_valid():
    df = generate_ai4i2020_dataset(n_samples=100, seed=42)
    valid, report = DatasetValidator.validate_dataframe(df)
    assert valid is True
    assert report["total_rows"] == 100
    assert report["quality_score"] > 90.0

def test_dataset_validator_missing_columns():
    df = pd.DataFrame({"some_col": [1, 2, 3]})
    valid, report = DatasetValidator.validate_dataframe(df)
    assert valid is False
    assert len(report["errors"]) > 0

def test_dataset_ingestion_to_db(db_session, tmp_path):
    df = generate_ai4i2020_dataset(n_samples=50, seed=42)
    csv_file = tmp_path / "test_telemetry.csv"
    df.to_csv(csv_file, index=False)

    result = DatasetValidator.ingest_csv_to_db(str(csv_file), db=db_session, machine_id="TEST-MACHINE", limit=30)
    assert result["success"] is True
    assert result["ingested_count"] == 30

    records = db_session.query(Telemetry).filter(Telemetry.machine_id == "TEST-MACHINE").all()
    assert len(records) == 30
