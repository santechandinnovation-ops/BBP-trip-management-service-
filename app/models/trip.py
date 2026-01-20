from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TripStatus(str, Enum):
    RECORDING = "RECORDING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"

class TripCreate(BaseModel):
    startTime: datetime

class CoordinateInput(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime
    elevation: Optional[float] = None

class TripComplete(BaseModel):
    endTime: datetime

class TripResponse(BaseModel):
    tripId: str
    userId: str
    startTime: datetime
    status: str

class CoordinateResponse(BaseModel):
    coordinateId: str
    message: str

class WeatherData(BaseModel):
    temperature: Optional[float] = None
    conditions: Optional[str] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    humidity: Optional[int] = None

class TripCompleteResponse(BaseModel):
    tripId: str
    status: str
    totalDistance: float
    duration: int
    averageSpeed: float
    maxSpeed: float
    weather: Optional[WeatherData] = None

class TripSummary(BaseModel):
    tripId: str
    startTime: datetime
    endTime: Optional[datetime]
    totalDistance: Optional[float]
    duration: Optional[int]
    averageSpeed: Optional[float]

class TripHistoryResponse(BaseModel):
    trips: List[TripSummary]
    total: int

class CoordinateDetail(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    elevation: Optional[float] = None

class TripDetail(BaseModel):
    tripId: str
    userId: str
    startTime: datetime
    endTime: Optional[datetime]
    totalDistance: Optional[float]
    duration: Optional[int]
    averageSpeed: Optional[float]
    maxSpeed: Optional[float]
    coordinates: List[CoordinateDetail]
    weather: Optional[WeatherData] = None
