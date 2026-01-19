# BBP Trip Management Service

Microservice for managing cycling trip recording, GPS tracking, statistics calculation, and weather data enrichment.

## Features

- Create and manage cycling trips
- Record GPS coordinates during active trips (every 5 seconds)
- Calculate trip statistics (distance, speed, duration)
- Enrich trips with current weather data (OpenWeatherMap free tier)
- View trip history and detailed trip information

## Weather API Note

⚠️ **Important**: This service uses OpenWeatherMap's **current weather endpoint** (`/data/2.5/weather`) which is available on the free tier, instead of the historical weather endpoint which requires a paid plan.

When a trip is completed, the service fetches the **current weather** at the trip location, not historical data. This is a limitation of the free tier but still provides useful weather context.

## Endpoints

All endpoints follow the DD specification exactly.

### Authenticated Endpoints (require JWT token)

#### POST /trips
Create a new trip (start recording).

#### POST /trips/:id/coordinates
Add GPS coordinate to active trip (called every 5 seconds by frontend).

#### PUT /trips/:id/complete
Mark trip as completed and calculate final statistics with weather enrichment.

#### GET /trips
Retrieve trip history for authenticated user.

#### GET /trips/:id
Retrieve detailed trip information including route coordinates and weather.

### Public Endpoints

#### GET /health
Health check endpoint.

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
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in credentials.

Get your OpenWeatherMap API key from: https://openweathermap.org/api

### 3. Initialize Database

```bash
python database/setup_db.py
```

### 4. Run the Service

```bash
uvicorn app.main:app --reload --port 8002
```

API documentation: http://localhost:8002/docs

## GPS Update Frequency

The frontend sends GPS coordinates every **5 seconds** during active trip recording.

## Statistics Calculation

Uses Haversine formula for accurate distance calculations.

## Weather Data Enrichment (R.10, R.11)

- Uses OpenWeatherMap free tier endpoint `/data/2.5/weather`
- Fetches current weather at trip location when trip completes
- Graceful degradation: trip saves without weather if API unavailable
- max_retries=2, timeout=5.0 seconds
