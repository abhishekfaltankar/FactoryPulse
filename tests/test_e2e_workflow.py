def test_end_to_end_factorypulse_workflow(client):
    # 1. System health check
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "online"

    # 2. Check fleet analytics
    analytics_res = client.get("/api/analytics/overview")
    assert analytics_res.status_code == 200
    assert analytics_res.json()["total_machines"] >= 5

    # 3. Register new production machine
    new_m = {
        "id": "MILL-900",
        "name": "5-Axis High Speed Gantry Mill",
        "model": "DMG MORI DMU 50",
        "machine_type": "H",
        "location": "Sector F - Titanium Wing",
        "status": "OPERATIONAL",
        "health_score": 100.0
    }
    create_m_res = client.post("/api/machines", json=new_m)
    assert create_m_res.status_code == 201

    # 4. Stream normal telemetry
    telemetry_normal = {
        "machine_id": "MILL-900",
        "air_temperature": 298.5,
        "process_temperature": 308.8,
        "rotational_speed": 1520.0,
        "torque": 41.0,
        "tool_wear": 25.0
    }
    t_res1 = client.post("/api/telemetry", json=telemetry_normal)
    assert t_res1.status_code == 201

    # Verify machine is still OPERATIONAL
    m_check1 = client.get("/api/machines/MILL-900")
    assert m_check1.json()["status"] == "OPERATIONAL"

    # 5. Stream severe failure condition (extreme power: high speed + extreme torque)
    telemetry_severe = {
        "machine_id": "MILL-900",
        "air_temperature": 299.0,
        "process_temperature": 309.0,
        "rotational_speed": 2700.0,
        "torque": 92.0,
        "tool_wear": 190.0
    }
    t_res2 = client.post("/api/telemetry", json=telemetry_severe)
    assert t_res2.status_code == 201

    # 6. Verify machine status updated to WARNING or CRITICAL
    m_check2 = client.get("/api/machines/MILL-900")
    assert m_check2.json()["status"] in ["WARNING", "CRITICAL"]

    # 7. Verify an active alert was auto-generated
    alerts_res = client.get("/api/alerts?machine_id=MILL-900&status=ACTIVE")
    assert alerts_res.status_code == 200
    active_alerts = alerts_res.json()
    assert len(active_alerts) > 0
    target_alert = active_alerts[0]

    # 8. Technician acknowledges the alert
    ack_res = client.put(f"/api/alerts/{target_alert['id']}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # 9. Schedule maintenance
    maint_payload = {
        "machine_id": "MILL-900",
        "technician": "David Bowman",
        "notes": "Emergency thermal and torque limiter replacement.",
        "status": "IN_PROGRESS",
        "cost": 890.0
    }
    maint_create = client.post("/api/maintenance", json=maint_payload)
    assert maint_create.status_code == 201
    maint_id = maint_create.json()["id"]

    # 10. Complete maintenance
    maint_complete = client.put(f"/api/maintenance/{maint_id}", json={"status": "COMPLETED"})
    assert maint_complete.status_code == 200

    # 11. Resolve the alert
    resolve_res = client.put(f"/api/alerts/{target_alert['id']}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # 12. Check that machine health is restored
    m_restored = client.get("/api/machines/MILL-900")
    assert m_restored.json()["status"] == "OPERATIONAL"
    assert m_restored.json()["health_score"] == 100.0

    # 13. Verify ML metadata endpoint
    meta_res = client.get("/api/train/metadata")
    assert meta_res.status_code == 200
    assert "metrics" in meta_res.json()
    assert meta_res.json()["metrics"]["accuracy"] > 0.85
