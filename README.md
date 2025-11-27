# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather data using the [Open-Meteo API](https://open-meteo.com/).

## Features
- `get_weather(city)`: Returns current temperature and wind speed for a given city.

## Installation

1.  Clone the repository.
2.  Install dependencies using `uv` (recommended) or `pip`:
    ```bash
    uv pip install -r requirements.txt
    ```

## Usage

Run the server:
```bash
uvicorn main:mcp --reload
```
(Note: `main:mcp` assumes FastMCP exposes the ASGI app as `mcp`. If using `fastmcp run`, follow FastMCP docs).

## Testing

Run tests with `pytest`:
```bash
pytest
```
