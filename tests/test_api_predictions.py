def test_predict_endpoint_normal(client):
    req = {
        "machine_id": "CNC-101",
        "machine_type": "M",
        "air_temperature": 298.2,
        "process_temperature": 308.7,
        "rotational_speed": 1500.0,
        "torque": 40.0,
        "tool_wear": 10.0
    }
    response = client.post("/api/predict", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "CNC-101"
    assert data["risk_level"] == "NORMAL"
    assert data["failure_probability"] < 0.50
    assert data["failure_mode"] == "No Failure"

def test_predict_endpoint_overstrain(client):
    # Severe torque * tool wear exceeding limits (> 12000 for M)
    req = {
        "machine_id": "CNC-101",
        "machine_type": "M",
        "air_temperature": 298.0,
        "process_temperature": 308.0,
        "rotational_speed": 1400.0,
        "torque": 75.0,
        "tool_wear": 240.0
    }
    response = client.post("/api/predict", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["failure_probability"] > 0.50
    assert data["risk_level"] in ["WARNING", "CRITICAL"]

def test_prediction_history(client):
    response = client.get("/api/predict/history/CNC-101?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
