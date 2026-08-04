from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class LocationModel(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    accuracy = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    battery = Column(Integer, nullable=True)
    timestamp = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)