import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.machine import Machine
from models.telemetry import Telemetry
from models.alert import Alert
from models.maintenance import MaintenanceRecord
from data.seed import seed_database

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_database_seeding(db_session):
    seed_database(db=db_session)
    
    machines = db_session.query(Machine).all()
    assert len(machines) == 5
    machine_ids = [m.id for m in machines]
    assert "CNC-101" in machine_ids
    assert "DRILL-301" in machine_ids

    telemetry = db_session.query(Telemetry).all()
    assert len(telemetry) == 5 * 15

    alerts = db_session.query(Alert).all()
    assert len(alerts) >= 2

    maintenance = db_session.query(MaintenanceRecord).all()
    assert len(maintenance) >= 2
