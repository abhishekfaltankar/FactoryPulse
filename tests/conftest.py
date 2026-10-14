import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from data.seed import seed_database
from main import app
from ml.predictor import PredictiveMaintenanceInferenceEngine

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="session")
def TestingSession(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session(test_engine, TestingSession):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSession(bind=connection)

    # Seed baseline fleet for tests
    seed_database(db=session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Ensure predictor is initialized
    PredictiveMaintenanceInferenceEngine.get_instance()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
