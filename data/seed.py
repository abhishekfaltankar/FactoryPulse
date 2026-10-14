import sys
import random
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.machine import Machine
from models.telemetry import Telemetry
from models.alert import Alert
from models.maintenance import MaintenanceRecord

INITIAL_MACHINES = [
    {
        "id": "CNC-101",
        "name": "High-Precision 5-Axis Milling Center",
        "model": "Hermle C42U",
        "machine_type": "H",
        "location": "Sector A - Aerospace Machining",
        "status": "OPERATIONAL",
        "health_score": 96.5,
    },
    {
        "id": "CNC-102",
        "name": "Vertical Machining Center",
        "model": "Haas VF-4SS",
        "machine_type": "M",
        "location": "Sector A - Heavy Milling",
        "status": "WARNING",
        "health_score": 72.0,
    },
    {
        "id": "LATHE-201",
        "name": "CNC Turning Center",
        "model": "Mazak Quick Turn 250MSY",
        "machine_type": "M",
        "location": "Sector B - Precision Turning",
        "status": "OPERATIONAL",
        "health_score": 91.0,
    },
    {
        "id": "DRILL-301",
        "name": "Automated Multi-Spindle Drill",
        "model": "Brother Speedio S700X1",
        "machine_type": "L",
        "location": "Sector C - Rapid Drilling",
        "status": "CRITICAL",
        "health_score": 45.2,
    },
    {
        "id": "PRESS-401",
        "name": "Hydraulic Stamping Press",
        "model": "Schuler T-200",
        "machine_type": "H",
        "location": "Sector D - Forming & Stamping",
        "status": "UNDER_MAINTENANCE",
        "health_score": 58.0,
    }
]

def seed_database(db: Session = None):
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Check if machines exist
        existing_machines = db.query(Machine).count()
        if existing_machines == 0:
            now = datetime.now(timezone.utc)
            for m_data in INITIAL_MACHINES:
                machine = Machine(
                    id=m_data["id"],
                    name=m_data["name"],
                    model=m_data["model"],
                    machine_type=m_data["machine_type"],
                    location=m_data["location"],
                    status=m_data["status"],
                    health_score=m_data["health_score"],
                    installed_at=now - timedelta(days=random.randint(180, 500)),
                    last_maintenance_date=now - timedelta(days=random.randint(15, 60))
                )
                db.add(machine)

            db.commit()

            # Add initial telemetry readings for each machine
            for m_data in INITIAL_MACHINES:
                m_id = m_data["id"]
                base_air = 298.0 + random.uniform(-1.0, 1.0)
                base_proc = base_air + 10.0 + random.uniform(-0.5, 1.5)
                base_speed = 1500.0 + random.uniform(-50, 50)
                base_torque = 40.0 + random.uniform(-5, 5)

                if m_data["status"] == "CRITICAL":
                    base_proc += 4.5
                    base_torque += 25.0

                for i in range(15):
                    t_time = now - timedelta(minutes=(15 - i) * 10)
                    reading = Telemetry(
                        machine_id=m_id,
                        timestamp=t_time,
                        air_temperature=round(base_air + random.uniform(-0.4, 0.4), 2),
                        process_temperature=round(base_proc + random.uniform(-0.5, 0.5), 2),
                        rotational_speed=round(base_speed + random.uniform(-30, 30), 1),
                        torque=round(base_torque + random.uniform(-3, 3), 2),
                        tool_wear=round(float(i * 12 + random.randint(0, 5)), 1)
                    )
                    db.add(reading)

            # Seed an alert for the critical and warning machines
            db.add(Alert(
                machine_id="DRILL-301",
                timestamp=now - timedelta(hours=2),
                severity="CRITICAL",
                message="High torque and abnormal process temperature delta detected. Severe failure risk.",
                status="ACTIVE"
            ))
            db.add(Alert(
                machine_id="CNC-102",
                timestamp=now - timedelta(hours=5),
                severity="HIGH",
                message="Elevated tool wear rate approaching replacement threshold (200 min).",
                status="ACTIVE"
            ))

            # Seed maintenance records
            db.add(MaintenanceRecord(
                machine_id="PRESS-401",
                scheduled_date=now - timedelta(hours=6),
                technician="Elena Rostova",
                notes="Quarterly hydraulic seal overhaul and high-pressure valve calibration.",
                status="IN_PROGRESS",
                cost=1250.00
            ))
            db.add(MaintenanceRecord(
                machine_id="CNC-101",
                scheduled_date=now - timedelta(days=25),
                completed_date=now - timedelta(days=25, hours=-2),
                technician="Marcus Chen",
                notes="Routine spindle lubrication and thermal sensor calibration.",
                status="COMPLETED",
                cost=420.00
            ))

            db.commit()
            print("Database successfully seeded with initial machines, telemetry, alerts, and maintenance records.")
        else:
            print(f"Database already contains {existing_machines} machines. Seeding skipped.")
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_database()
