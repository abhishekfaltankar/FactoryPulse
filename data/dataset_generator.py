import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DATASET_CSV_PATH, RAW_DATA_DIR

def generate_ai4i2020_dataset(n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic AI4I 2020 Predictive Maintenance Dataset following
    the physical parameters and failure mode rules of the UCI repository.
    """
    np.random.seed(seed)

    types = np.random.choice(["L", "M", "H"], size=n_samples, p=[0.50, 0.30, 0.20])
    product_ids = [f"{t}{np.random.randint(10000, 99999)}" for t in types]
    udis = np.arange(1, n_samples + 1)

    # Air temperature: normal centered at 300 K with std 2.0 K
    air_temp = np.random.normal(300.0, 2.0, size=n_samples)
    # Process temperature: generated as air temperature + 10 K + normal noise (std 1.0)
    process_temp = air_temp + 10.0 + np.random.normal(0.0, 1.0, size=n_samples)

    # Rotational speed: centered around 1538 rpm with std ~180 rpm, bounded
    rot_speed = np.random.normal(1538, 179, size=n_samples)
    rot_speed = np.clip(rot_speed, 1168, 2886)

    # Torque: normally distributed around 40.0 Nm with std 10.0 Nm
    torque = np.random.normal(40.0, 9.8, size=n_samples)
    torque = np.clip(torque, 3.8, 76.6)

    # Tool wear: uniformly distributed between 0 and 250 minutes
    tool_wear = np.random.uniform(0, 246, size=n_samples)

    # Physics-based failure modes
    # 1. Tool Wear Failure (TWF)
    twf = np.zeros(n_samples, dtype=int)
    twf_mask = (tool_wear >= 200) & (tool_wear <= 245)
    twf[twf_mask] = np.random.choice([0, 1], size=np.sum(twf_mask), p=[0.75, 0.25])

    # 2. Heat Dissipation Failure (HDF)
    # Fails if (Process temp - Air temp) < 8.6 K and Rotational speed < 1380 rpm
    temp_diff = process_temp - air_temp
    hdf = np.zeros(n_samples, dtype=int)
    hdf_mask = (temp_diff < 8.6) & (rot_speed < 1380)
    hdf[hdf_mask] = 1

    # 3. Power Failure (PWF)
    # Power = Torque * (Rotational speed * 2 * pi / 60)
    power_watts = torque * (rot_speed * 2 * np.pi / 60)
    pwf = np.zeros(n_samples, dtype=int)
    pwf_mask = (power_watts < 3500) | (power_watts > 9000)
    pwf[pwf_mask] = 1

    # 4. Overstrain Failure (OSF)
    # Product of tool wear and torque exceeds limits based on Type
    tool_torque = tool_wear * torque
    osf = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        limit = 11000 if types[i] == "L" else (12000 if types[i] == "M" else 13000)
        if tool_torque[i] > limit:
            osf[i] = 1

    # 5. Random Failures (RNF): 0.1% chance
    rnf = np.random.choice([0, 1], size=n_samples, p=[0.999, 0.001])

    # Overall Machine failure indicator
    machine_failure = ((twf | hdf | pwf | osf | rnf) > 0).astype(int)

    # Assign single primary failure type for classification
    failure_types = []
    for i in range(n_samples):
        if machine_failure[i] == 0:
            failure_types.append("No Failure")
        elif twf[i] == 1:
            failure_types.append("Tool Wear Failure")
        elif hdf[i] == 1:
            failure_types.append("Heat Dissipation Failure")
        elif pwf[i] == 1:
            failure_types.append("Power Failure")
        elif osf[i] == 1:
            failure_types.append("Overstrain Failure")
        elif rnf[i] == 1:
            failure_types.append("Random Failures")
        else:
            failure_types.append("No Failure")

    df = pd.DataFrame({
        "UDI": udis,
        "Product ID": product_ids,
        "Type": types,
        "Air temperature [K]": np.round(air_temp, 2),
        "Process temperature [K]": np.round(process_temp, 2),
        "Rotational speed [rpm]": np.round(rot_speed, 1),
        "Torque [Nm]": np.round(torque, 2),
        "Tool wear [min]": np.round(tool_wear, 1),
        "Machine failure": machine_failure,
        "TWF": twf,
        "HDF": hdf,
        "PWF": pwf,
        "OSF": osf,
        "RNF": rnf,
        "Failure Type": failure_types
    })

    return df

def ensure_dataset_exists(csv_path: Path = DATASET_CSV_PATH) -> pd.DataFrame:
    """Ensures the dataset exists on disk; creates it if absent."""
    if csv_path.exists():
        return pd.read_csv(csv_path)
    
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_ai4i2020_dataset()
    df.to_csv(csv_path, index=False)
    print(f"Generated realistic AI4I 2020 dataset and saved to {csv_path} ({len(df)} rows).")
    return df

if __name__ == "__main__":
    df = ensure_dataset_exists()
    print("Dataset preview:")
    print(df.head())
    print("\nMachine failure breakdown:")
    print(df["Failure Type"].value_counts())
