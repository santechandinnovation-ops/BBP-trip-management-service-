# BBP Trip Management Service

Microservice for managing cycling trip recording, GPS tracking, statistics calculation, and weather data enrichment.

## Features

- Create and manage cycling trips
- Record GPS coordinates during active trips (every 5 seconds)
- Calculate trip statistics (distance, speed, duration)
- Enrich trips with historical weather data
- View trip history and detailed trip information

## Endpoints

### Authenticated Endpoints (require JWT token)

#### POST /trips
Create a new trip (start recording).

**Request:**
```json
{
  "startTime": "2024-01-19T10:00:00Z"
}
```

**Response (201):**
```json
{
  "tripId": "uuid",
  "userId": "uuid",
  "startTime": "2024-01-19T10:00:00Z",
  "status": "RECORDING"
}
```

#### POST /trips/:id/coordinates
Add GPS coordinate to active trip (called every 5 seconds by frontend).

**Request:**
```json
{
  "latitude": 45.4642,
  "longitude": 9.1900,
  "timestamp": "2024-01-19T10:00:05Z",
  "elevation": 120.5
}
```

**Response (201):**
```json
{
  "coordinateId": "uuid",
  "message": "Coordinate added"
}
```

#### PUT /trips/:id/complete
Mark trip as completed and calculate final statistics.

**Request:**
```json
{
  "endTime": "2024-01-19T11:00:00Z"
}
```

**Response (200):**
```json
{
  "tripId": "uuid",
  "status": "COMPLETED",
  "totalDistance": 15.234,
  "duration": 3600,
  "averageSpeed": 15.23,
  "maxSpeed": 28.5,
  "weather": {
    "temperature": 18.5,
    "conditions": "clear sky",
    "windSpeed": 12.3,
    "windDirection": "NE"
  }
}
```

#### GET /trips
Retrieve trip history for authenticated user.

**Response (200):**
```json
{
  "trips": [
    {
      "tripId": "uuid",
      "startTime": "2024-01-19T10:00:00Z",
      "endTime": "2024-01-19T11:00:00Z",
      "totalDistance": 15.234,
      "duration": 3600,
      "averageSpeed": 15.23
    }
  ],
  "total": 1
}
```

#### GET /trips/:id
Retrieve detailed trip information including route coordinates.

**Response (200):**
```json
{
  "tripId": "uuid",
  "userId": "uuid",
  "startTime": "2024-01-19T10:00:00Z",
  "endTime": "2024-01-19T11:00:00Z",
  "totalDistance": 15.234,
  "duration": 3600,
  "averageSpeed": 15.23,
  "maxSpeed": 28.5,
  "coordinates": [
    {
      "latitude": 45.4642,
      "longitude": 9.1900,
      "timestamp": "2024-01-19T10:00:00Z",
      "elevation": 120.5
    }
  ],
  "weather": {
    "temperature": 18.5,
    "conditions": "clear sky",
    "windSpeed": 12.3,
    "windDirection": "NE"
  }
}
```

### Public Endpoints

#### GET /health
Health check endpoint.

**Response (200):**
```json
{
  "message": "healthy",
  "service": "BBP Trip Management Service",
  "timestamp": "2024-01-19T10:00:00Z",
  "version": "1.0.0"
}
```

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key
PORT=8002
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd trip-management-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:
- `DATABASE_URL`: Supabase PostgreSQL connection string
- `JWT_SECRET_KEY`: Same secret key used by User Management Service
- `OPENWEATHERMAP_API_KEY`: Get from https://openweathermap.org/api

### 3. Initialize Database

```bash
python database/setup_db.py
```

This creates the required tables:
- `trips`: Trip records with statistics
- `trip_coordinates`: GPS coordinates for each trip
- `trip_weather`: Weather data for completed trips

### 4. Run the Service

```bash
uvicorn app.main:app --reload --port 8002
```

The service will be available at http://localhost:8002

API documentation: http://localhost:8002/docs

## GPS Update Frequency

The frontend should send GPS coordinates every **5 seconds** during an active trip recording session.

## Statistics Calculation

Trip statistics are calculated using the Haversine formula:

- **Total Distance**: Sum of distances between consecutive GPS points
- **Duration**: Time difference between start and end
- **Average Speed**: Total distance / duration
- **Max Speed**: Maximum instantaneous speed between any two consecutive points

## Weather Data Enrichment

After trip completion, the service attempts to fetch historical weather data from OpenWeatherMap API. If the weather service is unavailable (R.11 - graceful degradation), the trip is saved without weather data.

## Testing

Run the test script:

```bash
python test_trip_service.py
```

## Deployment on Railway

1. Create a new project on Railway
2. Connect your Git repository
3. Railway will detect the `Procfile` automatically
4. Set environment variables in Railway dashboard
5. Deploy!

## Database Schema

### trips
- trip_id (UUID, PK)
- user_id (UUID, FK)
- start_time (TIMESTAMP)
- end_time (TIMESTAMP, nullable)
- total_distance (NUMERIC, nullable)
- duration (INTEGER, nullable)
- average_speed (NUMERIC, nullable)
- max_speed (NUMERIC, nullable)
- status (ENUM: RECORDING, COMPLETED)
- created_date (TIMESTAMP)

### trip_coordinates
- coordinate_id (UUID, PK)
- trip_id (UUID, FK)
- latitude (NUMERIC)
- longitude (NUMERIC)
- timestamp (TIMESTAMP)
- elevation (NUMERIC, nullable)
- sequence_order (INTEGER)

### trip_weather
- weather_id (UUID, PK)
- trip_id (UUID, FK, UNIQUE)
- temperature (NUMERIC)
- conditions (VARCHAR)
- wind_speed (NUMERIC)
- wind_direction (VARCHAR)
- humidity (INTEGER)

## License

MIT
