# BBP Trip Management Service

Microservice for recording and managing bike trips.

## Overview

Handles trip lifecycle from creation to completion, including GPS coordinate tracking, distance calculation, weather data integration, and trip statistics. Uses PostgreSQL for data persistence.

## Features

- **Trip Recording**: Start/stop trip sessions
- **GPS Tracking**: Store coordinate batches during trips
- **Distance Calculation**: Haversine formula for accurate distances
- **Weather Integration**: Fetch weather data for trip location
- **Trip Statistics**: Duration, distance, average speed
- **Trip History**: Query past trips with filtering

## Tech Stack

- FastAPI
- PostgreSQL (psycopg2)
- HTTPX (weather API)
- Python-Jose (JWT)

## API Endpoints

| Method | Endpoint                        | Description           |
|--------|---------------------------------|-----------------------|
| GET    | `/health`                       | Health check          |
| POST   | `/trips`                        | Create new trip       |
| GET    | `/trips`                        | List user trips       |
| GET    | `/trips/{id}`                   | Get trip details      |
| POST   | `/trips/{id}/coordinates`       | Add single coordinate |
| POST   | `/trips/{id}/coordinates/batch` | Add coordinate batch  |
| POST   | `/trips/{id}/complete`          | Complete trip         |
| DELETE | `/trips/{id}`                   | Delete trip           |

## Database Tables

- `trips` - Trip metadata and statistics
- `trip_coordinates` - GPS coordinates per trip

## Environment Variables

```
DATABASE_URL=<postgresql-url>
JWT_SECRET_KEY=<secret-key>
WEATHER_API_KEY=<openweather-key>
```

## Running Locally

```bash
pip install -r requirements.txt
python database/setup_db.py  # Initialize tables
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Deployment

Deployed on Railway. See `Procfile` for startup command.
