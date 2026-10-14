def test_ingest_telemetry_normal(client):
    reading = {
        "machine_id": "CNC-101",
        "air_temperature": 298.1,
        "process_temperature": 308.6,
        "rotational_speed": 1551.0,
        "torque": 42.8,
        "tool_wear": 15.0
    }
    response = client.post("/api/telemetry", json=reading)
    assert response.status_code == 201
    data = response.json()
    assert data["machine_id"] == "CNC-101"
    assert "id" in data

def test_ingest_telemetry_critical_auto_alert(client):
    # Extreme torque and speed causing power failure condition (> 9000 W)
    critical_reading = {
        "machine_id": "CNC-101",
        "air_temperature": 298.0,
        "process_temperature": 308.0,
        "rotational_speed": 2800.0,
        "torque": 90.0,
        "tool_wear": 180.0
    }
    response = client.post("/api/telemetry", json=critical_reading)
    assert response.status_code == 201

    # Machine should now have downgraded health score and alert created
    m_res = client.get("/api/machines/CNC-101")
    assert m_res.status_code == 200
    m_data = m_res.json()
    assert m_data["status"] in ["WARNING", "CRITICAL"]

    # Check alert was created
    alerts_res = client.get("/api/alerts?machine_id=CNC-101&status=ACTIVE")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
    assert any("Failure" in a["message"] for a in alerts)

def test_get_machine_telemetry(client):
    response = client.get("/api/telemetry/CNC-101?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["machine_id"] == "CNC-101"

def test_batch_ingest_telemetry(client):
    batch = {
        "readings": [
            {
                "machine_id": "LATHE-201",
                "air_temperature": 299.0,
                "process_temperature": 309.0,
                "rotational_speed": 1500.0,
                "torque": 38.0,
                "tool_wear": 5.0
            },
            {
                "machine_id": "LATHE-201",
                "air_temperature": 299.1,
                "process_temperature": 309.2,
                "rotational_speed": 1505.0,
                "torque": 38.2,
                "tool_wear": 6.0
            }
        ]
    }
    response = client.post("/api/telemetry/batch", json=batch)
    assert response.status_code == 201
    assert response.json()["ingested_count"] == 2
