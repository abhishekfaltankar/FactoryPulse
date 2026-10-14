from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from database import Base

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(String(50), ForeignKey("machines.id"), nullable=False, index=True)
    scheduled_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_date = Column(DateTime, nullable=True)
    technician = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="SCHEDULED") # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    cost = Column(Float, nullable=False, default=0.0)
