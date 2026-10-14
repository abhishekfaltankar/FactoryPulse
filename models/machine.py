from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float
from database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    machine_type = Column(String(50), nullable=False, default="M") # L, M, H
    location = Column(String(100), nullable=False, default="Sector 1")
    status = Column(String(50), nullable=False, default="OPERATIONAL") # OPERATIONAL, WARNING, CRITICAL, UNDER_MAINTENANCE
    installed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_maintenance_date = Column(DateTime, nullable=True)
    health_score = Column(Float, default=100.0)
