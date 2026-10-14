from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(String(50), ForeignKey("machines.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    air_temperature = Column(Float, nullable=False) # Kelvin
    process_temperature = Column(Float, nullable=False) # Kelvin
    rotational_speed = Column(Float, nullable=False) # RPM
    torque = Column(Float, nullable=False) # Nm
    tool_wear = Column(Float, nullable=False) # minutes
