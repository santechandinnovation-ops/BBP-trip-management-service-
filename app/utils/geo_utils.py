import math
from typing import List, Tuple, Union
from datetime import datetime
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    calcualte distance between two coords using haversine formula
    returns METERS not km for more acuracy
    """
    R = 6371000  # earth radius in meters
    
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance  # Returns meters


def parse_timestamp(ts: Union[str, datetime]) -> datetime:
    """convert timestmp to datetime obj, handles diferent formats"""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return date_parser.parse(ts)
        except Exception as e:
            logger.error(f"Failed to parse timestamp '{ts}': {e}")
            raise ValueError(f"Invalid timestamp format: {ts}")
    raise ValueError(f"Unsupported timestamp type: {type(ts)}")


def calculate_speed_ms(distance_meters: float, time_seconds: float) -> float:
    """calc speed in m/s given distance and time"""
    if time_seconds <= 0:
        return 0.0
    return distance_meters / time_seconds


def calculate_trip_statistics(coordinates: List[Tuple]) -> dict:
    """
    calc trip stats from list of (lat, lon, timestamp) tuples
    
    returns dict with:
        - total_distance: meters
        - duration: seconds  
        - average_speed: m/s
        - max_speed: m/s (uses 3-segmnet moving avg to filter out gps spikes)
    """
    if len(coordinates) < 2:
        return {
            "total_distance": 0.0,
            "duration": 0,
            "average_speed": 0.0,
            "max_speed": 0.0
        }
    
    total_distance = 0.0
    max_speed = 0.0
    segment_speeds = []  # store all valid speeds for moving avg later
    
    # parse all the timestamps first
    parsed_coords = []
    for coord in coordinates:
        lat, lon, ts = coord[0], coord[1], coord[2]
        try:
            parsed_ts = parse_timestamp(ts)
            parsed_coords.append((float(lat), float(lon), parsed_ts))
        except Exception as e:
            logger.warning(f"Skipping coordinate with invalid timestamp: {e}")
            continue
    
    if len(parsed_coords) < 2:
        return {
            "total_distance": 0.0,
            "duration": 0,
            "average_speed": 0.0,
            "max_speed": 0.0
        }
    
    # sort by timestamp to make sure theyre in right order
    parsed_coords.sort(key=lambda x: x[2])
    
    for i in range(len(parsed_coords) - 1):
        lat1, lon1, time1 = parsed_coords[i]
        lat2, lon2, time2 = parsed_coords[i + 1]
        
        # calc segment distance in meters
        segment_distance = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        
        # skip tiny movements (probly just gps noise) - less than 1m
        if segment_distance < 1:
            continue
            
        time_diff = (time2 - time1).total_seconds()
        
        # skip if time diff is too small or negative (somthing weird)
        if time_diff <= 0:
            continue
        
        total_distance += segment_distance
        
        # calc segment speed in m/s
        segment_speed = calculate_speed_ms(segment_distance, time_diff)
        
        # filter unrealistic speeds (> 20m/s = 72km/h is crazy fast for a bike)
        # this helps filter out gps jumps and errors
        if segment_speed < 20:  # 20 m/s = 72 km/h max reasonable bike speed
            segment_speeds.append(segment_speed)
    
    # calc max speed using 3-segment moving avg to smooth out device shakes
    # this way momentry gps spikes dont mess up the max speed
    if len(segment_speeds) >= 3:
        for i in range(len(segment_speeds) - 2):
            window_avg = (segment_speeds[i] + segment_speeds[i+1] + segment_speeds[i+2]) / 3
            max_speed = max(max_speed, window_avg)
    elif len(segment_speeds) > 0:
        # for short trips just use max of availble speeds
        max_speed = max(segment_speeds)
    
    # calc duration from first to last timestamp
    start_time = parsed_coords[0][2]
    end_time = parsed_coords[-1][2]
    duration = int((end_time - start_time).total_seconds())
    
    # calc average speed
    if duration > 0 and total_distance > 0:
        average_speed = total_distance / duration
    else:
        average_speed = 0.0
    
    logger.info(f"Trip stats: distance={total_distance:.2f}m, duration={duration}s, "
                f"avg_speed={average_speed:.2f}m/s, max_speed={max_speed:.2f}m/s")
    
    return {
        "total_distance": round(total_distance, 2),  # meters
        "duration": duration,  # seconds
        "average_speed": round(average_speed, 2),  # m/s
        "max_speed": round(max_speed, 2)  # m/s
    }
