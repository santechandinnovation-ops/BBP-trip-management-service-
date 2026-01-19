-- Create ENUM types for Trip Management
DO $$
BEGIN
    BEGIN
        CREATE TYPE trip_status AS ENUM ('RECORDING', 'PAUSED', 'FINISHED', 'CANCELLED');
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Type trip_status already exists, skipping creation';
    END;
END $$;

-- Trips table
CREATE TABLE IF NOT EXISTS trips (
    trip_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_distance NUMERIC(10, 3),
    duration INTEGER,
    average_speed NUMERIC(6, 2),
    max_speed NUMERIC(6, 2),
    status trip_status NOT NULL DEFAULT 'RECORDING',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TripCoordinates table
CREATE TABLE IF NOT EXISTS trip_coordinates (
    coordinate_id UUID PRIMARY KEY,
    trip_id UUID NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    elevation NUMERIC(8, 2),
    sequence_order INTEGER NOT NULL,
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180)
);

-- TripWeather table
CREATE TABLE IF NOT EXISTS trip_weather (
    weather_id UUID PRIMARY KEY,
    trip_id UUID NOT NULL UNIQUE REFERENCES trips(trip_id) ON DELETE CASCADE,
    temperature NUMERIC(5, 2),
    conditions VARCHAR(100),
    wind_speed NUMERIC(6, 2),
    wind_direction VARCHAR(50),
    humidity INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status);
CREATE INDEX IF NOT EXISTS idx_trip_coordinates_trip_id ON trip_coordinates(trip_id);
CREATE INDEX IF NOT EXISTS idx_trip_coordinates_timestamp ON trip_coordinates(timestamp);
CREATE INDEX IF NOT EXISTS idx_trip_weather_trip_id ON trip_weather(trip_id);
