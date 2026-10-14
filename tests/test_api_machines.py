def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "healthy"

def test_get_machines(client):
    response = client.get("/api/machines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    ids = [m["id"] for m in data]
    assert "CNC-101" in ids

def test_get_machine_by_id(client):
    response = client.get("/api/machines/CNC-101")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "CNC-101"
    assert "name" in data
    assert "health_score" in data

def test_get_machine_not_found(client):
    response = client.get("/api/machines/NON-EXISTENT-999")
    assert response.status_code == 404

def test_create_machine(client):
    new_machine = {
        "id": "ROBOT-501",
        "name": "Articulated Robotic Arm",
        "model": "KUKA KR 16",
        "machine_type": "H",
        "location": "Sector E - Assembly",
        "status": "OPERATIONAL",
        "health_score": 98.0
    }
    response = client.post("/api/machines", json=new_machine)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "ROBOT-501"

    # Verify retrieval
    get_res = client.get("/api/machines/ROBOT-501")
    assert get_res.status_code == 200

def test_update_machine(client):
    update_data = {
        "status": "WARNING",
        "health_score": 68.5
    }
    response = client.put("/api/machines/CNC-101", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "WARNING"
    assert data["health_score"] == 68.5
