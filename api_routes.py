from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from database import get_db
from models import WeatherStation, WeatherData
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Pydantic models for API responses
class WeatherStationResponse(BaseModel):
    id: int
    code: str
    name: str
    state: str
    elevation: float
    latitude: float
    longitude: float
    is_active: bool
    data_source: str
    
    class Config:
        from_attributes = True

class WeatherDataResponse(BaseModel):
    id: int
    station_code: str
    station_name: str
    timestamp: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    wind_speed: Optional[float]
    precipitation: Optional[float]
    weather_description: Optional[str]
    
    class Config:
        from_attributes = True

@router.get("/stations", response_model=List[WeatherStationResponse])
async def get_weather_stations(db: Session = Depends(get_db)):
    """Get all weather stations with their coordinates"""
    
    # Query stations with coordinates
    result = db.execute(text("""
        SELECT s.id, s.code, s.name, s.state, s.elevation, s.is_active, s.data_source,
               ST_Y(s.location) as latitude, ST_X(s.location) as longitude
        FROM weather_stations s
        ORDER BY s.name
    """))
    
    stations = []
    for row in result:
        stations.append(WeatherStationResponse(
            id=row.id,
            code=row.code,
            name=row.name,
            state=row.state,
            elevation=row.elevation,
            latitude=row.latitude,
            longitude=row.longitude,
            is_active=row.is_active,
            data_source=row.data_source
        ))
    
    return stations

@router.get("/stations/{station_code}", response_model=WeatherStationResponse)
async def get_station_by_code(station_code: str, db: Session = Depends(get_db)):
    """Get a specific weather station by code"""
    
    result = db.execute(text("""
        SELECT s.id, s.code, s.name, s.state, s.elevation, s.is_active, s.data_source,
               ST_Y(s.location) as latitude, ST_X(s.location) as longitude
        FROM weather_stations s
        WHERE s.code = :code
    """), {"code": station_code})
    
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Weather station not found")
    
    return WeatherStationResponse(
        id=row.id,
        code=row.code,
        name=row.name,
        state=row.state,
        elevation=row.elevation,
        latitude=row.latitude,
        longitude=row.longitude,
        is_active=row.is_active,
        data_source=row.data_source
    )

@router.get("/weather/recent", response_model=List[WeatherDataResponse])
async def get_recent_weather(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent weather data across all stations"""
    
    recent_data = (db.query(WeatherData, WeatherStation)
                   .join(WeatherStation)
                   .order_by(WeatherData.timestamp.desc())
                   .limit(limit)
                   .all())
    
    weather_list = []
    for data, station in recent_data:
        weather_list.append(WeatherDataResponse(
            id=data.id,
            station_code=station.code,
            station_name=station.name,
            timestamp=data.timestamp,
            temperature=data.temperature,
            humidity=data.humidity,
            pressure=data.pressure,
            wind_speed=data.wind_speed,
            precipitation=data.precipitation,
            weather_description=data.weather_description
        ))
    
    return weather_list

@router.get("/weather/station/{station_code}", response_model=List[WeatherDataResponse])
async def get_weather_by_station(station_code: str, limit: int = 50, db: Session = Depends(get_db)):
    """Get weather data for a specific station"""
    
    # Check if station exists
    station = db.query(WeatherStation).filter(WeatherStation.code == station_code).first()
    if not station:
        raise HTTPException(status_code=404, detail="Weather station not found")
    
    # Get weather data
    weather_data = (db.query(WeatherData)
                    .filter(WeatherData.station_id == station.id)
                    .order_by(WeatherData.timestamp.desc())
                    .limit(limit)
                    .all())
    
    weather_list = []
    for data in weather_data:
        weather_list.append(WeatherDataResponse(
            id=data.id,
            station_code=station.code,
            station_name=station.name,
            timestamp=data.timestamp,
            temperature=data.temperature,
            humidity=data.humidity,
            pressure=data.pressure,
            wind_speed=data.wind_speed,
            precipitation=data.precipitation,
            weather_description=data.weather_description
        ))
    
    return weather_list

@router.get("/weather/nearby")
async def get_nearby_stations(lat: float, lng: float, radius_km: float = 100, db: Session = Depends(get_db)):
    """Find weather stations within a specified radius of a location"""
    
    result = db.execute(text("""
        SELECT s.code, s.name, s.state,
               ST_Y(s.location) as latitude, ST_X(s.location) as longitude,
               ST_Distance(
                   ST_Transform(s.location, 3857),
                   ST_Transform(ST_GeomFromText('POINT(' || :lng || ' ' || :lat || ')', 4326), 3857)
               ) / 1000 as distance_km
        FROM weather_stations s
        WHERE ST_Distance(
            ST_Transform(s.location, 3857),
            ST_Transform(ST_GeomFromText('POINT(' || :lng || ' ' || :lat || ')', 4326), 3857)
        ) <= :radius_m
        ORDER BY distance_km
    """), {"lat": lat, "lng": lng, "radius_m": radius_km * 1000})
    
    stations = []
    for row in result:
        stations.append({
            "code": row.code,
            "name": row.name,
            "state": row.state,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "distance_km": round(row.distance_km, 2)
        })
    
    return {
        "search_location": {"latitude": lat, "longitude": lng},
        "radius_km": radius_km,
        "stations_found": len(stations),
        "stations": stations
    }

@router.get("/statistics")
async def get_weather_statistics(db: Session = Depends(get_db)):
    """Get overall weather statistics"""
    
    # Basic counts
    station_count = db.query(WeatherStation).count()
    data_count = db.query(WeatherData).count()
    
    # Temperature statistics
    temp_stats = db.query(
        func.min(WeatherData.temperature).label('min_temp'),
        func.max(WeatherData.temperature).label('max_temp'),
        func.avg(WeatherData.temperature).label('avg_temp')
    ).first()
    
    # Date range
    date_range = db.query(
        func.min(WeatherData.timestamp).label('min_date'),
        func.max(WeatherData.timestamp).label('max_date')
    ).first()
    
    return {
        "stations": station_count,
        "total_records": data_count,
        "temperature": {
            "min": temp_stats.min_temp,
            "max": temp_stats.max_temp,
            "average": round(temp_stats.avg_temp, 1) if temp_stats.avg_temp else None
        },
        "date_range": {
            "from": date_range.min_date,
            "to": date_range.max_date
        }
    }
