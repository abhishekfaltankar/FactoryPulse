import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.telemetry import Telemetry
from models.machine import Machine

REQUIRED_COLUMNS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]"
]

VALID_RANGES = {
    "Air temperature [K]": (270.0, 350.0),
    "Process temperature [K]": (270.0, 360.0),
    "Rotational speed [rpm]": (500.0, 4000.0),
    "Torque [Nm]": (0.0, 150.0),
    "Tool wear [min]": (0.0, 400.0)
}

class DatasetValidator:
    """
    Validates industrial telemetry datasets and handles data ingestion
    with physical bounds checks, schema verification, and quality reporting.
    """

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        errors: List[str] = []
        warnings: List[str] = []

        total_rows = len(df)
        if total_rows == 0:
            return False, {
                "valid": False,
                "total_rows": 0,
                "errors": ["Dataset is completely empty."],
                "warnings": [],
                "quality_score": 0.0
            }

        # Check required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return False, {
                "valid": False,
                "total_rows": total_rows,
                "errors": errors,
                "warnings": warnings,
                "quality_score": 0.0
            }

        # Check null values
        null_counts = df[REQUIRED_COLUMNS].isnull().sum().to_dict()
        total_nulls = sum(null_counts.values())
        if total_nulls > 0:
            warnings.append(f"Found {total_nulls} null values across required columns: {null_counts}")

        # Check bounds
        out_of_bounds_counts = {}
        for col, (min_val, max_val) in VALID_RANGES.items():
            out_bounds = ((df[col] < min_val) | (df[col] > max_val)).sum()
            if out_bounds > 0:
                out_of_bounds_counts[col] = int(out_bounds)

        if out_of_bounds_counts:
            warnings.append(f"Values out of physical range: {out_of_bounds_counts}")

        # Physics check: Process temperature should generally exceed or equal air temperature
        inverted_temp = (df["Process temperature [K]"] < df["Air temperature [K]"]).sum()
        if inverted_temp > 0:
            warnings.append(f"{inverted_temp} rows have Process temperature < Air temperature.")

        # Duplicate check
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate rows.")

        # Compute a quality score (0 - 100)
        penalty = (total_nulls / (total_rows * len(REQUIRED_COLUMNS))) * 50
        oob_total = sum(out_of_bounds_counts.values())
        penalty += (oob_total / (total_rows * len(REQUIRED_COLUMNS))) * 50
        quality_score = max(0.0, round(100.0 - penalty, 2))

        valid = len(errors) == 0

        report = {
            "valid": valid,
            "total_rows": total_rows,
            "errors": errors,
            "warnings": warnings,
            "quality_score": quality_score,
            "column_stats": {
                col: {
                    "mean": float(df[col].mean()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "min": float(df[col].min()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "max": float(df[col].max()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "nulls": int(null_counts.get(col, 0))
                } for col in REQUIRED_COLUMNS
            }
        }
        return valid, report

    @staticmethod
    def ingest_csv_to_db(csv_path: str, db: Session, machine_id: str = "CNC-101", limit: int = 500) -> Dict[str, Any]:
        """Ingests validated telemetry rows from CSV into the database."""
        df = pd.read_csv(csv_path)
        valid, report = DatasetValidator.validate_dataframe(df)
        if not valid:
            raise ValueError(f"Dataset validation failed: {report['errors']}")

        # Ensure machine exists
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            machine = Machine(
                id=machine_id,
                name=f"Ingested Unit {machine_id}",
                model="Standard Industrial Unit",
                machine_type="M",
                location="Sector A",
                status="OPERATIONAL"
            )
            db.add(machine)
            db.commit()

        # Ingest rows
        rows_to_ingest = df.head(limit)
        now = datetime.now(timezone.utc)
        records = []
        for idx, row in rows_to_ingest.iterrows():
            reading = Telemetry(
                machine_id=machine_id,
                timestamp=now,
                air_temperature=float(row["Air temperature [K]"]),
                process_temperature=float(row["Process temperature [K]"]),
                rotational_speed=float(row["Rotational speed [rpm]"]),
                torque=float(row["Torque [Nm]"]),
                tool_wear=float(row["Tool wear [min]"])
            )
            records.append(reading)

        db.bulk_save_objects(records)
        db.commit()

        return {
            "success": True,
            "ingested_count": len(records),
            "machine_id": machine_id,
            "quality_score": report["quality_score"],
            "validation_report": report
        }
