from fastmcp import FastMCP
import httpx
import structlog
from contextlib import asynccontextmanager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Global HTTP client
http_client: httpx.AsyncClient | None = None

@asynccontextmanager
async def lifespan(server: FastMCP):
    global http_client
    logger.info("Initializing HTTP client")
    http_client = httpx.AsyncClient()
    yield
    logger.info("Closing HTTP client")
    await http_client.aclose()

# Initialize FastMCP with lifespan
mcp = FastMCP("weather", lifespan=lifespan)

async def get_http_client() -> httpx.AsyncClient:
    """Returns the global HTTP client, creating it if necessary (fallback)."""
    global http_client
    if http_client is None:
        logger.warning("HTTP client not initialized in lifespan, creating temporary client")
        return httpx.AsyncClient()
    return http_client

async def get_weather_logic(city: str, client: httpx.AsyncClient) -> str:
    """
    Core logic for fetching weather.
    """
    log = logger.bind(city=city)
    log.info("Fetching weather data")

    # 1. Geocoding
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
    
    try:
        geo_resp = await client.get(geo_url, params=geo_params)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
    except httpx.HTTPError as e:
        log.error("Geocoding API error", error=str(e))
        return f"Error fetching geocoding data: {str(e)}"

    if not geo_data.get("results"):
        log.warning("City not found")
        raise ValueError(f"City not found: {city}")

    location = geo_data["results"][0]
    lat = location["latitude"]
    lng = location["longitude"]
    name = location["name"]
    
    log = log.bind(lat=lat, lng=lng, name=name)

    # 2. Weather
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat, 
        "longitude": lng, 
        "current_weather": "true"
    }

    try:
        weather_resp = await client.get(weather_url, params=weather_params)
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()
    except httpx.HTTPError as e:
        log.error("Weather API error", error=str(e))
        return f"Error fetching weather data: {str(e)}"

    current = weather_data.get("current_weather", {})
    temp = current.get("temperature")
    wind = current.get("windspeed")
    
    log.info("Weather fetched successfully", temp=temp, wind=wind)

    return f"Current weather in {name}: {temp}°C, Wind: {wind}km/h"

@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get the current weather for a given city.
    """
    client = await get_http_client()
    # If the client was created temporarily (fallback), we should close it, but for now let's rely on lifespan.
    # If get_http_client returns the global one, we don't close it here.
    return await get_weather_logic(city, client)

if __name__ == "__main__":
    mcp.run()
