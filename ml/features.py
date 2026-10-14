import numpy as np
import pandas as pd
from typing import Dict, Any, List, Union

FEATURE_NAMES = [
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
    "temperature_difference",
    "power_watts",
    "torque_wear_product",
    "speed_torque_ratio",
    "temp_ratio",
    "type_H",
    "type_L",
    "type_M"
]

def engineer_features(data: Union[pd.DataFrame, Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforms raw telemetry data into engineered physics-based features.
    Accepts either a pandas DataFrame or a single dictionary.
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data.copy()

    # Normalize column names if coming from raw AI4I dataset
    rename_map = {
        "Air temperature [K]": "air_temperature",
        "Process temperature [K]": "process_temperature",
        "Rotational speed [rpm]": "rotational_speed",
        "Torque [Nm]": "torque",
        "Tool wear [min]": "tool_wear",
        "Type": "machine_type"
    }
    df = df.rename(columns=rename_map)

    # Ensure required base numeric fields exist
    base_cols = ["air_temperature", "process_temperature", "rotational_speed", "torque", "tool_wear"]
    for col in base_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required numeric column for feature engineering: '{col}'")
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # If machine_type / type is missing, default to 'M'
    if "machine_type" not in df.columns and "Type" not in df.columns:
        df["machine_type"] = "M"
    elif "machine_type" not in df.columns and "Type" in df.columns:
        df["machine_type"] = df["Type"]

    df["machine_type"] = df["machine_type"].fillna("M").astype(str).str.upper()

    # Derived physics features
    df["temperature_difference"] = df["process_temperature"] - df["air_temperature"]
    df["power_watts"] = df["torque"] * (df["rotational_speed"] * 2.0 * np.pi / 60.0)
    df["torque_wear_product"] = df["torque"] * df["tool_wear"]
    df["speed_torque_ratio"] = df["rotational_speed"] / (df["torque"] + 1e-5)
    df["temp_ratio"] = df["process_temperature"] / (df["air_temperature"] + 1e-5)

    # One-hot encode machine_type for L, M, H
    df["type_H"] = (df["machine_type"] == "H").astype(float)
    df["type_L"] = (df["machine_type"] == "L").astype(float)
    df["type_M"] = (df["machine_type"] == "M").astype(float)

    return df[FEATURE_NAMES]
