from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from datetime import datetime
import logging

from app.models.trip import (
    TripCreate, TripResponse, CoordinateInput, CoordinateResponse,
    TripComplete, TripCompleteResponse, TripHistoryResponse, TripDetail,
    TripSummary, CoordinateDetail, WeatherData
)
from app.utils.security import get_current_user
from app.utils.geo_utils import calculate_trip_statistics
from app.services.weather_service import fetch_historical_weather
from app.config.database import db
from app.utils.exceptions import (
    TripNotFoundException, TripAlreadyCompletedException,
    UnauthorizedTripAccessException, NoCoordinatesException
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/trips", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new trip (start recording)."""
    trip_id = str(uuid.uuid4())

    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trips (trip_id, user_id, start_time, status, created_date)
            VALUES (%s, %s, %s, 'RECORDING', CURRENT_TIMESTAMP)
        """, (trip_id, user_id, trip_data.startTime))

        conn.commit()
        cursor.close()

        return TripResponse(
            tripId=trip_id,
            userId=user_id,
            startTime=trip_data.startTime,
            status="RECORDING"
        )

    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating trip: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trip"
        )
    finally:
        db.return_connection(conn)

@router.post("/trips/{trip_id}/coordinates", response_model=CoordinateResponse, status_code=status.HTTP_201_CREATED)
async def add_coordinate(
    trip_id: str,
    coordinate: CoordinateInput,
    user_id: str = Depends(get_current_user)
):
    """Add GPS coordinate to active trip."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        # Verify trip exists and belongs to user
        cursor.execute("""
            SELECT user_id, status FROM trips WHERE trip_id = %s
        """, (trip_id,))

        result = cursor.fetchone()

        if not result:
            raise TripNotFoundException("Trip not found")

        trip_user_id, trip_status = result

        if trip_user_id != user_id:
            raise UnauthorizedTripAccessException("User does not own this trip")

        if trip_status != 'RECORDING':
            raise TripAlreadyCompletedException("Trip already completed")

        # Get next sequence order
        cursor.execute("""
            SELECT COALESCE(MAX(sequence_order), 0) + 1
            FROM trip_coordinates
            WHERE trip_id = %s
        """, (trip_id,))

        sequence_order = cursor.fetchone()[0]

        # Insert coordinate
        coordinate_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO trip_coordinates
            (coordinate_id, trip_id, latitude, longitude, timestamp, elevation, sequence_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            coordinate_id,
            trip_id,
            coordinate.latitude,
            coordinate.longitude,
            coordinate.timestamp,
            coordinate.elevation,
            sequence_order
        ))

        conn.commit()
        cursor.close()

        return CoordinateResponse(
            coordinateId=coordinate_id,
            message="Coordinate added"
        )

    except TripNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    except UnauthorizedTripAccessException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own this trip"
        )
    except TripAlreadyCompletedException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trip already completed"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding coordinate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add coordinate"
        )
    finally:
        db.return_connection(conn)

@router.put("/trips/{trip_id}/complete", response_model=TripCompleteResponse)
async def complete_trip(
    trip_id: str,
    trip_complete: TripComplete,
    user_id: str = Depends(get_current_user)
):
    """Mark trip as completed and calculate final statistics."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        # Verify trip exists and belongs to user
        cursor.execute("""
            SELECT user_id, status FROM trips WHERE trip_id = %s
        """, (trip_id,))

        result = cursor.fetchone()

        if not result:
            raise TripNotFoundException("Trip not found")

        trip_user_id, trip_status = result

        if trip_user_id != user_id:
            raise UnauthorizedTripAccessException("User does not own this trip")

        if trip_status != 'RECORDING':
            raise TripAlreadyCompletedException("Trip already completed")

        # Get all coordinates for this trip
        cursor.execute("""
            SELECT latitude, longitude, timestamp
            FROM trip_coordinates
            WHERE trip_id = %s
            ORDER BY sequence_order
        """, (trip_id,))

        coordinates = cursor.fetchall()

        if len(coordinates) < 1:
            raise NoCoordinatesException("Trip has no coordinates")

        # Calculate statistics
        stats = calculate_trip_statistics(coordinates)

        # Update trip with statistics
        cursor.execute("""
            UPDATE trips
            SET end_time = %s,
                status = 'COMPLETED',
                total_distance = %s,
                duration = %s,
                average_speed = %s,
                max_speed = %s
            WHERE trip_id = %s
        """, (
            trip_complete.endTime,
            stats['total_distance'],
            stats['duration'],
            stats['average_speed'],
            stats['max_speed'],
            trip_id
        ))

        # Try to fetch weather data
        weather_data = None
        if coordinates:
            # Use middle coordinate and timestamp for weather
            mid_idx = len(coordinates) // 2
            mid_lat, mid_lon, mid_time = coordinates[mid_idx]

            try:
                weather_result = await fetch_historical_weather(mid_lat, mid_lon, mid_time)

                if weather_result:
                    # Insert weather data
                    weather_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO trip_weather
                        (weather_id, trip_id, temperature, conditions, wind_speed, wind_direction, humidity)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        weather_id,
                        trip_id,
                        weather_result.get('temperature'),
                        weather_result.get('conditions'),
                        weather_result.get('wind_speed'),
                        weather_result.get('wind_direction'),
                        weather_result.get('humidity')
                    ))

                    weather_data = WeatherData(**weather_result)
            except Exception as e:
                logger.warning(f"Weather service error (non-blocking): {e}")

        conn.commit()
        cursor.close()

        return TripCompleteResponse(
            tripId=trip_id,
            status="COMPLETED",
            totalDistance=stats['total_distance'],
            duration=stats['duration'],
            averageSpeed=stats['average_speed'],
            maxSpeed=stats['max_speed'],
            weather=weather_data
        )

    except TripNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    except UnauthorizedTripAccessException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own this trip"
        )
    except TripAlreadyCompletedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trip already completed"
        )
    except NoCoordinatesException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trip has no coordinates"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Error completing trip: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete trip"
        )
    finally:
        db.return_connection(conn)

@router.get("/trips", response_model=TripHistoryResponse)
async def get_trip_history(user_id: str = Depends(get_current_user)):
    """Retrieve trip history for authenticated user."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT trip_id, start_time, end_time, total_distance, duration, average_speed
            FROM trips
            WHERE user_id = %s AND status = 'COMPLETED'
            ORDER BY start_time DESC
        """, (user_id,))

        results = cursor.fetchall()
        cursor.close()

        trips = []
        for row in results:
            trips.append(TripSummary(
                tripId=str(row[0]),
                startTime=row[1],
                endTime=row[2],
                totalDistance=float(row[3]) if row[3] else None,
                duration=row[4],
                averageSpeed=float(row[5]) if row[5] else None
            ))

        return TripHistoryResponse(
            trips=trips,
            total=len(trips)
        )

    except Exception as e:
        logger.error(f"Error fetching trip history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trip history"
        )
    finally:
        db.return_connection(conn)

@router.get("/trips/{trip_id}", response_model=TripDetail)
async def get_trip_detail(
    trip_id: str,
    user_id: str = Depends(get_current_user)
):
    """Retrieve detailed trip information including route coordinates."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        # Get trip data
        cursor.execute("""
            SELECT user_id, start_time, end_time, total_distance, duration,
                   average_speed, max_speed
            FROM trips
            WHERE trip_id = %s
        """, (trip_id,))

        trip_result = cursor.fetchone()

        if not trip_result:
            raise TripNotFoundException("Trip not found")

        trip_user_id = trip_result[0]

        if trip_user_id != user_id:
            raise UnauthorizedTripAccessException("User does not own this trip")

        # Get coordinates
        cursor.execute("""
            SELECT latitude, longitude, timestamp, elevation
            FROM trip_coordinates
            WHERE trip_id = %s
            ORDER BY sequence_order
        """, (trip_id,))

        coord_results = cursor.fetchall()

        coordinates = [
            CoordinateDetail(
                latitude=float(row[0]),
                longitude=float(row[1]),
                timestamp=row[2],
                elevation=float(row[3]) if row[3] else None
            )
            for row in coord_results
        ]

        # Get weather data
        cursor.execute("""
            SELECT temperature, conditions, wind_speed, wind_direction
            FROM trip_weather
            WHERE trip_id = %s
        """, (trip_id,))

        weather_result = cursor.fetchone()
        weather_data = None

        if weather_result:
            weather_data = WeatherData(
                temperature=float(weather_result[0]) if weather_result[0] else None,
                conditions=weather_result[1],
                windSpeed=float(weather_result[2]) if weather_result[2] else None,
                windDirection=weather_result[3]
            )

        cursor.close()

        return TripDetail(
            tripId=trip_id,
            userId=str(trip_result[0]),
            startTime=trip_result[1],
            endTime=trip_result[2],
            totalDistance=float(trip_result[3]) if trip_result[3] else None,
            duration=trip_result[4],
            averageSpeed=float(trip_result[5]) if trip_result[5] else None,
            maxSpeed=float(trip_result[6]) if trip_result[6] else None,
            coordinates=coordinates,
            weather=weather_data
        )

    except TripNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    except UnauthorizedTripAccessException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own this trip"
        )
    except Exception as e:
        logger.error(f"Error fetching trip detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trip detail"
        )
    finally:
        db.return_connection(conn)
