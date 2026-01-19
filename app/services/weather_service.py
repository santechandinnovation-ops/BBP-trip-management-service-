import httpx
import logging
from typing import Optional, Dict
from datetime import datetime
from app.config.settings import settings
logger = logging.getLogger(__name__)
async def fetch_current_weather(
    latitude: float,
    longitude: float
) -> Optional[Dict]:
    """
    Fetch historical weather data from OpenWeatherMap API.
    Returns weather data dict or None if service unavailable.
    """
    if not settings.OPENWEATHERMAP_API_KEY:
        logger.warning("OpenWeatherMap API key not configured")
        return None
    # OpenWeatherMap Current Weather API endpoint (Free plan)
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric" # Use Celsius
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
                    weather = data.get("weather", [{}])[0]
                    return {
                        "temperature": data.get("main", {}).get("temp"),
                        "conditions": weather.get("description", ""),
                        "wind_speed": data.get("wind", {}).get("speed"),
                        "wind_direction": get_wind_direction(data.get("wind", {}).get("deg", 0)),
                        "humidity": data.get("main", {}).get("humidity")
                    }
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
