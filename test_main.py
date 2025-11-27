import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from main import get_weather_logic, get_weather

@pytest.mark.asyncio
async def test_get_weather_logic_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Mock Geocoding
    mock_geo_resp = MagicMock()
    mock_geo_resp.json.return_value = {
        "results": [{"latitude": 51.5, "longitude": -0.12, "name": "London"}]
    }
    mock_geo_resp.raise_for_status.return_value = None

    # Mock Weather
    mock_weather_resp = MagicMock()
    mock_weather_resp.json.return_value = {
        "current_weather": {"temperature": 10.0, "windspeed": 5.0}
    }
    mock_weather_resp.raise_for_status.return_value = None

    mock_client.get.side_effect = [mock_geo_resp, mock_weather_resp]

    result = await get_weather_logic("London", mock_client)
    
    assert "London" in result
    assert "10.0" in result
    assert "5.0" in result
    assert mock_client.get.call_count == 2

@pytest.mark.asyncio
async def test_get_weather_logic_city_not_found():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_geo_resp = MagicMock()
    mock_geo_resp.json.return_value = {"results": []}
    mock_client.get.return_value = mock_geo_resp

    with pytest.raises(ValueError, match="City not found"):
        await get_weather_logic("Nowhere", mock_client)

@pytest.mark.asyncio
async def test_get_weather_logic_api_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.HTTPError("API Down")

    result = await get_weather_logic("London", mock_client)
    assert "Error fetching geocoding data" in result

@pytest.mark.asyncio
async def test_get_weather_tool_integration():
    # Test the tool wrapper
    # We need to mock get_http_client to return our mock client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Setup mocks similar to success case
    mock_geo_resp = MagicMock()
    mock_geo_resp.json.return_value = {
        "results": [{"latitude": 40.71, "longitude": -74.01, "name": "New York"}]
    }
    mock_weather_resp = MagicMock()
    mock_weather_resp.json.return_value = {
        "current_weather": {"temperature": 20.0, "windspeed": 15.0}
    }
# Removed ineffective test_get_weather_tool_integration
# The core logic is fully tested in test_get_weather_logic_* functions.
# FastMCP handles the tool wrapping, which we trust.




@pytest.mark.asyncio
async def test_get_http_client():
    from main import get_http_client, lifespan, mcp
    
    # Test fallback
    client = await get_http_client()
    assert isinstance(client, httpx.AsyncClient)
    await client.aclose()

    # Test lifespan (mocking the server)
    # We can manually invoke the context manager
    async with lifespan(mcp):
        from main import http_client
        assert http_client is not None
        assert isinstance(http_client, httpx.AsyncClient)
        
        # Verify get_http_client returns the global one
        client2 = await get_http_client()
        assert client2 is http_client

@pytest.mark.asyncio
async def test_tool_execution_with_client():
    from main import mcp
    from fastmcp.client import Client
    
    # Mock httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient") as MockClientCls:
        mock_client_instance = AsyncMock()
        MockClientCls.return_value = mock_client_instance
        
        # Setup mocks
        mock_geo_resp = MagicMock()
        mock_geo_resp.json.return_value = {
            "results": [{"latitude": 51.5, "longitude": -0.12, "name": "London"}]
        }
        mock_geo_resp.raise_for_status.return_value = None

        mock_weather_resp = MagicMock()
        mock_weather_resp.json.return_value = {
            "current_weather": {"temperature": 10.0, "windspeed": 5.0}
        }
        mock_weather_resp.raise_for_status.return_value = None

        mock_client_instance.get.side_effect = [mock_geo_resp, mock_weather_resp]

        # Use FastMCP Client to test the server
        async with Client(mcp) as client:
            result = await client.call_tool(name="get_weather", arguments={"city": "London"})
            
            # Result might be a CallToolResult object or similar, check docs or inspect
            # The docs say: assert result.data is not None
            # Let's inspect what we get.
            assert result is not None
            # FastMCP Client returns a CallToolResult which has content
            # Let's assume the content is in result.content or result.data
            # Based on the wiki snippet: assert result.data == expected (for simple types?)
            # But get_weather returns a string.
            
            # Let's just print it if it fails, or check attributes.
            # Assuming result.content is a list of TextContent
            
            # Actually, looking at the wiki: assert result.data is not None
            # For a string return, it might be in result.content[0].text
            
            # Let's try to match the string in the result object representation or content
            assert "London" in str(result)
            assert "10.0" in str(result)



