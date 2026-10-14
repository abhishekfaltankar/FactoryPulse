import pytest
import numpy as np
import pandas as pd
from ml.features import engineer_features, FEATURE_NAMES
from ml.trainer import train_predictive_maintenance_model
from ml.predictor import PredictiveMaintenanceInferenceEngine

def test_feature_engineering_structure():
    sample_data = {
        "air_temperature": 298.1,
        "process_temperature": 308.6,
        "rotational_speed": 1551.0,
        "torque": 42.8,
        "tool_wear": 10.0,
        "machine_type": "M"
    }
    feats = engineer_features(sample_data)
    assert isinstance(feats, pd.DataFrame)
    assert list(feats.columns) == FEATURE_NAMES
    assert round(feats["temperature_difference"].iloc[0], 1) == 10.5
    assert feats["type_M"].iloc[0] == 1.0
    assert feats["type_L"].iloc[0] == 0.0

def test_inference_engine_normal_reading():
    engine = PredictiveMaintenanceInferenceEngine.get_instance()
    normal_input = {
        "machine_id": "CNC-101",
        "machine_type": "M",
        "air_temperature": 298.0,
        "process_temperature": 308.5,
        "rotational_speed": 1500.0,
        "torque": 40.0,
        "tool_wear": 20.0
    }
    result = engine.predict(normal_input)
    assert "failure_predicted" in result
    assert "failure_probability" in result
    assert "failure_mode" in result
    assert "risk_level" in result
    assert result["risk_level"] in ["NORMAL", "WARNING", "CRITICAL"]
    assert 0.0 <= result["failure_probability"] <= 1.0
    # Normal machine should have low failure probability
    assert result["failure_probability"] < 0.5
    assert result["failure_mode"] == "No Failure"

def test_inference_engine_extreme_power_failure():
    engine = PredictiveMaintenanceInferenceEngine.get_instance()
    # Power = torque * (speed * 2 * pi / 60) -> Torque 100 * speed 2500 rpm = 26,179 Watts (> 9000 W -> PWF)
    extreme_power_input = {
        "machine_id": "DRILL-301",
        "machine_type": "L",
        "air_temperature": 298.0,
        "process_temperature": 308.0,
        "rotational_speed": 2600.0,
        "torque": 95.0,
        "tool_wear": 150.0
    }
    result = engine.predict(extreme_power_input)
    assert result["failure_probability"] > 0.60
    assert result["risk_level"] in ["WARNING", "CRITICAL"]
    assert result["failure_mode"] in ["Power Failure", "Overstrain Failure"]

def test_inference_engine_batch_predict():
    engine = PredictiveMaintenanceInferenceEngine.get_instance()
    batch_input = [
        {
            "air_temperature": 298.0,
            "process_temperature": 308.0,
            "rotational_speed": 1500.0,
            "torque": 40.0,
            "tool_wear": 10.0,
            "machine_type": "M"
        },
        {
            "air_temperature": 302.0,
            "process_temperature": 303.0,
            "rotational_speed": 1200.0,
            "torque": 80.0,
            "tool_wear": 240.0,
            "machine_type": "H"
        }
    ]
    results = engine.batch_predict(batch_input)
    assert len(results) == 2
    assert results[0]["failure_probability"] < results[1]["failure_probability"]
