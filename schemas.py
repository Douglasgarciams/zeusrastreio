from pydantic import BaseModel
from typing import Optional

class LocationCreate(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    battery: Optional[int] = None
    timestamp: str