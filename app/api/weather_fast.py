# app/api/weather_fast.py
from fastapi import APIRouter, Depends, Response
import asyncio
from app.deps.http import get_client
from app.utils.cache import get, set_

router = APIRouter()

def grid_key(lat: float, lon: float, grid=0.1) -> str:
    latk = round(lat / grid) * grid
    lonk = round(lon / grid) * grid
    return f"wx:{latk:.3f},{lonk:.3f}"

@router.get("/weather")
async def weather(lat: float, lon: float, response: Response, client=Depends(get_client)):
    key = grid_key(lat, lon)

    # 命中则直接返回
    hit = get(key, ttl=600)
    if hit:
        response.headers["X-Cache"] = "HIT"
        response.headers["Cache-Control"] = "public, max-age=60"
        return hit

    async def openmeteo():
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m"
        }
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()

    # 可以并发更多外部调用
    om = await openmeteo()
    payload = {"openmeteo": om}

    set_(key, payload, ttl=600)
    response.headers["X-Cache"] = "MISS"
    response.headers["Cache-Control"] = "public, max-age=60"
    return payload
