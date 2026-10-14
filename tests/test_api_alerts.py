def test_get_alerts(client):
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_create_and_acknowledge_and_resolve_alert(client):
    new_alert = {
        "machine_id": "CNC-101",
        "severity": "HIGH",
        "message": "Vibration harmonics exceeding standard ISO 10816 limits."
    }
    create_res = client.post("/api/alerts", json=new_alert)
    assert create_res.status_code == 201
    alert_id = create_res.json()["id"]
    assert create_res.json()["status"] == "ACTIVE"

    # Acknowledge
    ack_res = client.put(f"/api/alerts/{alert_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"
    assert ack_res.json()["acknowledged_at"] is not None

    # Resolve
    resolve_res = client.put(f"/api/alerts/{alert_id}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["resolved_at"] is not None
