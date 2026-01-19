import httpx
import logging
from typing import Optional, Dict
from datetime import datetime
from app.config.settings import settings

logger = logging.getLogger(__name__)

async def fetch_historical_weather(
    latitude: float,
    longitude: float,
    timestamp: datetime
) -> Optional[Dict]:
    """
    Fetch historical weather data from OpenWeatherMap API.
    Returns weather data dict or None if service unavailable.
    """
    if not settings.OPENWEATHERMAP_API_KEY:
        logger.warning("OpenWeatherMap API key not configured")
        return None

    # OpenWeatherMap Time Machine API endpoint
    url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"

    # Convert datetime to Unix timestamp
    dt = int(timestamp.timestamp())

    params = {
        "lat": latitude,
        "lon": longitude,
        "dt": dt,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric"  # Use Celsius
    }

    max_retries = 2
    timeout = 5.0

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    # Extract relevant weather data
                    if "data" in data and len(data["data"]) > 0:
                        weather_data = data["data"][0]

                        return {
                            "temperature": weather_data.get("temp"),
                            "conditions": weather_data.get("weather", [{}])[0].get("description", ""),
                            "wind_speed": weather_data.get("wind_speed"),
                            "wind_direction": get_wind_direction(weather_data.get("wind_deg", 0)),
                            "humidity": weather_data.get("humidity")
                        }

                    return None

                elif response.status_code >= 500:
                    # Server error, retry
                    logger.warning(f"Weather API server error (attempt {attempt + 1}): {response.status_code}")
                    continue
                else:
                    # Client error, don't retry
                    logger.error(f"Weather API client error: {response.status_code}")
                    return None

        except httpx.TimeoutException:
            logger.warning(f"Weather API timeout (attempt {attempt + 1})")
            continue
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None

    logger.warning("Weather API unavailable after retries")
    return None

def get_wind_direction(degrees: float) -> str:
    """Convert wind direction degrees to cardinal direction."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]
