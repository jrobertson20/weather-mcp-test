from fastmcp import FastMCP
from fastapi import Depends
import httpx

# Initialize FastMCP
mcp = FastMCP("weather")

async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client

from typing import Annotated, Any

async def get_weather_logic(city: str, client: httpx.AsyncClient) -> str:
    """
    Core logic for fetching weather.
    """
    # 1. Geocoding
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
    
    try:
        geo_resp = await client.get(geo_url, params=geo_params)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
    except httpx.HTTPError as e:
        return f"Error fetching geocoding data: {str(e)}"

    if not geo_data.get("results"):
        raise ValueError(f"City not found: {city}")

    location = geo_data["results"][0]
    lat = location["latitude"]
    lng = location["longitude"]
    name = location["name"]

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
        return f"Error fetching weather data: {str(e)}"

    current = weather_data.get("current_weather", {})
    temp = current.get("temperature")
    wind = current.get("windspeed")

    return f"Current weather in {name}: {temp}°C, Wind: {wind}km/h"

@mcp.tool()
async def get_weather(city: str, client: Annotated[Any, Depends(get_http_client)]) -> str:
    """
    Get the current weather for a given city.
    """
    return await get_weather_logic(city, client)
