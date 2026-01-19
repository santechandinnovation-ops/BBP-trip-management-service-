import math
from typing import List, Tuple
from datetime import datetime

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula. Returns distance in kilometers."""
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    return distance

def calculate_speed(distance_km: float, time_seconds: float) -> float:
    """Calculate speed in km/h given distance in km and time in seconds."""
    if time_seconds <= 0:
        return 0.0
    hours = time_seconds / 3600
    speed_kmh = distance_km / hours
    return speed_kmh

def calculate_trip_statistics(coordinates: List[Tuple[float, float, datetime]]) -> dict:
    """Calculate trip statistics from list of (latitude, longitude, timestamp) tuples."""
    if len(coordinates) < 2:
        return {
            "total_distance": 0.0,
            "duration": 0,
            "average_speed": 0.0,
            "max_speed": 0.0
        }
    
    total_distance = 0.0
    max_speed = 0.0
    
    for i in range(len(coordinates) - 1):
        lat1, lon1, time1 = coordinates[i]
        lat2, lon2, time2 = coordinates[i + 1]
        segment_distance = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        total_distance += segment_distance
        time_diff = (time2 - time1).total_seconds()
        if time_diff > 0:
            segment_speed = calculate_speed(segment_distance, time_diff)
            max_speed = max(max_speed, segment_speed)
    
    start_time = coordinates[0][2]
    end_time = coordinates[-1][2]
    duration = int((end_time - start_time).total_seconds())
    average_speed = calculate_speed(total_distance, duration) if duration > 0 else 0.0
    
    return {
        "total_distance": round(total_distance, 3),
        "duration": duration,
        "average_speed": round(average_speed, 2),
        "max_speed": round(max_speed, 2)
    }
