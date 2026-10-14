from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(String(50), ForeignKey("machines.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    failure_predicted = Column(Integer, nullable=False) # 0 or 1
    failure_probability = Column(Float, nullable=False) # 0.0 to 1.0
    failure_mode = Column(String(100), nullable=False, default="No Failure")
    confidence_score = Column(Float, nullable=False, default=1.0)
    model_version = Column(String(50), nullable=False, default="v1.0")
    features = Column(Text, nullable=True) # JSON representation of input features
