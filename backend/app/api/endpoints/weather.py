from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.core.redis import cache_get, cache_set, cache_key_builder
from app.services.weather_service import WeatherService
from app.schemas.weather import (
    WeatherStationResponse,
    WeatherObservationResponse,
    WeatherDataFilter,
    WeatherDataExport
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/stations", response_model=List[WeatherStationResponse])
async def get_weather_stations(
    state: Optional[str] = Query(None, description="Filter by state"),
    source: Optional[str] = Query(None, description="Filter by data source (BOM, Meteostat)"),
    active_only: bool = Query(True, description="Only return active stations"),
    limit: int = Query(100, le=1000, description="Maximum number of stations to return"),
    offset: int = Query(0, ge=0, description="Number of stations to skip"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of weather stations"""
    cache_key = cache_key_builder("stations", state, source, active_only, limit, offset)
    
    # Try to get from cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        return cached_data
    
    weather_service = WeatherService(db)
    stations = await weather_service.get_stations(
        state=state,
        source=source,
        active_only=active_only,
        limit=limit,
        offset=offset
    )
    
    # Cache the result
    await cache_set(cache_key, stations, ttl=3600)  # Cache for 1 hour
    
    return stations


@router.get("/stations/{station_id}", response_model=WeatherStationResponse)
async def get_weather_station(
    station_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific weather station details"""
    cache_key = cache_key_builder("station", station_id)
    
    # Try cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        return cached_data
    
    weather_service = WeatherService(db)
    station = await weather_service.get_station_by_id(station_id)
    
    if not station:
        raise HTTPException(status_code=404, detail="Weather station not found")
    
    # Cache the result
    await cache_set(cache_key, station, ttl=7200)  # Cache for 2 hours
    
    return station


@router.get("/observations", response_model=List[WeatherObservationResponse])
async def get_weather_observations(
    station_ids: Optional[List[str]] = Query(None, description="Station IDs to filter by"), # 
    start_date: Optional[datetime] = Query(None, description="Start date for observations"),
    end_date: Optional[datetime] = Query(None, description="End date for observations"),
    variables: Optional[List[str]] = Query(None, description="Weather variables to include"),
    limit: int = Query(1000, le=10000, description="Maximum number of observations"),
    offset: int = Query(0, ge=0, description="Number of observations to skip"),
    db: AsyncSession = Depends(get_db)
):
    """Get weather observations with filtering"""
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=7)  # Default to last 7 days
    
    # Validate date range
    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    cache_key = cache_key_builder(
        "observations", 
        station_ids, 
        start_date.isoformat(), 
        end_date.isoformat(), 
        variables, 
        limit, 
        offset
    )
    
    # Try cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        return cached_data
    
    weather_service = WeatherService(db)
    observations = await weather_service.get_observations(
        station_ids=station_ids,
        start_date=start_date,
        end_date=end_date,
        variables=variables,
        limit=limit,
        offset=offset
    )
    
    # Cache for shorter time since weather data updates frequently
    await cache_set(cache_key, observations, ttl=1800)  # Cache for 30 minutes
    
    return observations


@router.get("/observations/latest", response_model=List[WeatherObservationResponse])
async def get_latest_observations(
    station_ids: Optional[List[str]] = Query(None, description="Station IDs to filter by"),
    hours: int = Query(24, le=168, description="Hours back from now to get latest observations"),
    db: AsyncSession = Depends(get_db)
):
    """Get latest weather observations"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)
    
    cache_key = cache_key_builder("latest_observations", station_ids, hours)
    
    # Try cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        return cached_data
    
    weather_service = WeatherService(db)
    observations = await weather_service.get_latest_observations(
        station_ids=station_ids,
        hours_back=hours
    )
    
    # Cache for short time since this is latest data
    await cache_set(cache_key, observations, ttl=600)  # Cache for 10 minutes
    
    return observations


@router.get("/observations/statistics")
async def get_weather_statistics(
    station_ids: Optional[List[str]] = Query(None, description="Station IDs to filter by"),
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    variables: Optional[List[str]] = Query(["temperature", "humidity", "pressure"], description="Variables to calculate statistics for"),
    aggregation: str = Query("daily", regex="^(hourly|daily|weekly|monthly)$", description="Aggregation period"),
    db: AsyncSession = Depends(get_db)
):
    """Get weather statistics and aggregations"""
    
    # Set default date range
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
    
    cache_key = cache_key_builder(
        "statistics", 
        station_ids, 
        start_date.isoformat(), 
        end_date.isoformat(), 
        variables, 
        aggregation
    )
    
    # Try cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        return cached_data
    
    weather_service = WeatherService(db)
    statistics = await weather_service.get_weather_statistics(
        station_ids=station_ids,
        start_date=start_date,
        end_date=end_date,
        variables=variables,
        aggregation=aggregation
    )
    
    # Cache statistics for longer since they don't change often
    await cache_set(cache_key, statistics, ttl=7200)  # Cache for 2 hours
    
    return statistics


@router.post("/refresh")
async def refresh_weather_data(
    sources: Optional[List[str]] = Query(["BOM"], description="Data sources to refresh"),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger weather data refresh from external APIs"""
    
    try:
        weather_service = WeatherService(db)
        result = await weather_service.refresh_weather_data(sources=sources)
        
        logger.info(f"Weather data refresh completed", sources=sources, result=result)
        
        return {
            "message": "Weather data refresh completed",
            "sources": sources,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Weather data refresh failed", error=str(e), sources=sources)
        raise HTTPException(status_code=500, detail=f"Failed to refresh weather data: {str(e)}")


@router.get("/geojson")
async def get_weather_geojson(
    station_ids: Optional[List[str]] = Query(None, description="Station IDs to include"),
    include_latest_data: bool = Query(True, description="Include latest observation data"),
    db: AsyncSession = Depends(get_db)
):
    """Get weather stations as GeoJSON for mapping"""
    
    cache_key = cache_key_builder("geojson", station_ids, include_latest_data)
    
    # Try cache first
    cached_data = await cache_get(cache_key)
    if cached_data:
        return cached_data
    
    weather_service = WeatherService(db)
    geojson_data = await weather_service.get_stations_geojson(
        station_ids=station_ids,
        include_latest_data=include_latest_data
    )
    
    # Cache GeoJSON data
    await cache_set(cache_key, geojson_data, ttl=1800)  # Cache for 30 minutes
    
    return geojson_data
