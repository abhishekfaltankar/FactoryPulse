def test_get_maintenance(client):
    response = client.get("/api/maintenance")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_schedule_and_complete_maintenance(client):
    new_task = {
        "machine_id": "CNC-102",
        "technician": "Sarah Connor",
        "notes": "Replace worn cutter head and calibrate axes.",
        "status": "SCHEDULED",
        "cost": 550.0
    }
    create_res = client.post("/api/maintenance", json=new_task)
    assert create_res.status_code == 201
    rec_id = create_res.json()["id"]

    # Update to IN_PROGRESS
    update_res = client.put(f"/api/maintenance/{rec_id}", json={"status": "IN_PROGRESS"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "IN_PROGRESS"

    # Complete maintenance
    complete_res = client.put(f"/api/maintenance/{rec_id}", json={"status": "COMPLETED", "cost": 620.0})
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
    assert complete_res.json()["completed_date"] is not None

    # Machine should now be reset to OPERATIONAL with 100.0 health
    m_res = client.get("/api/machines/CNC-102")
    assert m_res.status_code == 200
    assert m_res.json()["status"] == "OPERATIONAL"
    assert m_res.json()["health_score"] == 100.0
