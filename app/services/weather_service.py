import httpx
import logging
from typing import Optional, Dict
from app.config.settings import settings

logger = logging.getLogger(__name__)

async def fetch_current_weather(
    latitude: float,
    longitude: float
) -> Optional[Dict]:
    """
    fetch current wether data from openweathermap api
    returns weather dict or None if servise unavailable
    """
    if not settings.OPENWEATHERMAP_API_KEY:
        logger.warning("OpenWeatherMap API key not configured")
        return None

    # openweathermap api endpoint (using free tier)
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric"  # use celsius
    }

    max_retries = 2
    timeout = 5.0

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    # get the importent weather data from response
                    return {
                        "temperature": data["main"]["temp"],
                        "conditions": data["weather"][0]["description"],
                        "wind_speed": data["wind"]["speed"],
                        "wind_direction": get_wind_direction(data["wind"]["deg"]),
                        "humidity": data["main"]["humidity"]
                    }

                elif response.status_code >= 500:
                    # server error so we retry
                    logger.warning(f"Weather API server error (attempt {attempt + 1}): {response.status_code}")
                    continue
                else:
                    # client error dont retry
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
    """convert wind degrees to cardinal direciton like N, NE etc"""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]
