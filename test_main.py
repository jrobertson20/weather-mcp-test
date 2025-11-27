import pytest
from unittest.mock import AsyncMock, MagicMock
from fastmcp import FastMCP
from fastapi.testclient import TestClient
import httpx
from main import mcp, get_http_client

# We can't easily test FastMCP tools directly with TestClient because they are not standard FastAPI endpoints.
# However, we can test the underlying logic if we extract it, or we can try to invoke the tool via the mcp object if it exposes a way.
# FastMCP tools are registered as functions. We can import the function directly if we know its name, 
# but FastMCP wraps them.
# A better approach for unit testing the logic is to extract the logic into a function that takes the client, 
# and test that function.
# But `main.py` will have `get_weather` decorated with `@mcp.tool()`.
# We can call the decorated function directly in many frameworks. Let's assume FastMCP allows calling the decorated function.

@pytest.mark.asyncio
async def test_get_weather_success():
    # Mock the HTTP client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Mock Geocoding Response
    mock_geocoding_resp = MagicMock()
    mock_geocoding_resp.json.return_value = {
        "results": [
            {"latitude": 48.85, "longitude": 2.35, "name": "Paris"}
        ]
    }
    mock_geocoding_resp.raise_for_status.return_value = None

    # Mock Weather Response
    mock_weather_resp = MagicMock()
    mock_weather_resp.json.return_value = {
        "current_weather": {
            "temperature": 15.5,
            "windspeed": 10.2
        }
    }
    mock_weather_resp.raise_for_status.return_value = None

    # Setup side effects for client.get
    # First call is geocoding, second is weather
    mock_client.get.side_effect = [mock_geocoding_resp, mock_weather_resp]

    # Import the logic function
    from main import get_weather_logic

    # Call the logic directly
    result = await get_weather_logic(city="Paris", client=mock_client)

    # Verify result
    assert "Paris" in result
    assert "15.5" in result
    assert "10.2" in result

    # Verify API calls
    assert mock_client.get.call_count == 2
    
    # Check first call (Geocoding)
    call1_args = mock_client.get.call_args_list[0]
    assert "geocoding-api.open-meteo.com" in call1_args[0][0]
    assert call1_args[1]["params"]["name"] == "Paris"

    # Check second call (Weather)
    call2_args = mock_client.get.call_args_list[1]
    assert "api.open-meteo.com" in call2_args[0][0]
    assert call2_args[1]["params"]["latitude"] == 48.85
    assert call2_args[1]["params"]["longitude"] == 2.35

@pytest.mark.asyncio
async def test_get_weather_city_not_found():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Mock Geocoding Response (No results)
    mock_geocoding_resp = MagicMock()
    mock_geocoding_resp.json.return_value = {} # Or {"results": []} depending on API
    mock_geocoding_resp.raise_for_status.return_value = None

    mock_client.get.return_value = mock_geocoding_resp

    from main import get_weather_logic

    # Expect an error or a specific message
    # Let's assume we raise ValueError for now as per plan
    with pytest.raises(ValueError, match="City not found"):
        await get_weather_logic(city="UnknownCity", client=mock_client)
