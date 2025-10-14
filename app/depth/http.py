# app/deps/http.py
import httpx
from httpx import Timeout, AsyncHTTPTransport

_client: httpx.AsyncClient | None = None

async def startup_http():
    global _client
    _client = httpx.AsyncClient(
        timeout=Timeout(connect=2, read=5, write=5),
        transport=AsyncHTTPTransport(retries=2),
        headers={"User-Agent": "nsw-weather-dashboard/1.0"}
    )

async def shutdown_http():
    global _client
    if _client:
        await _client.aclose()
        _client = None

def get_client() -> httpx.AsyncClient:
    assert _client is not None, "HTTP client not initialized"
    return _client
