#!/usr/bin/env python3
"""
Database Demonstration Script
Shows that our database is working with real data
"""
import asyncio
import json
from database import get_db
from models import WeatherStation, WeatherData
from sqlalchemy import func, text
from datetime import datetime, timedelta

async def demonstrate_database():
    """Demonstrate that our database is working with real data"""
    print("🔍 Weather Database Demonstration")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # 1. Show total counts
        print("\n📊 DATABASE OVERVIEW:")
        station_count = db.query(WeatherStation).count()
        data_count = db.query(WeatherData).count()
        print(f"   ✅ Weather Stations: {station_count}")
        print(f"   ✅ Weather Records: {data_count:,}")
        
        # 2. Show some weather stations with their coordinates
        print("\n🏢 WEATHER STATIONS (with spatial data):")
        stations_with_coords = db.execute(text("""
            SELECT name, code, state, 
                   ST_Y(location) as latitude, 
                   ST_X(location) as longitude,
                   elevation
            FROM weather_stations 
            ORDER BY name 
            LIMIT 5
        """)).fetchall()
        
        for station in stations_with_coords:
            print(f"   🌡️ {station.name} ({station.code})")
            print(f"      📍 Location: {station.latitude:.3f}, {station.longitude:.3f}")
            print(f"      🏔️ Elevation: {station.elevation}m | State: {station.state}")
            print()
        
        # 3. Show recent weather data
        print("🌤️ RECENT WEATHER READINGS:")
        recent_weather = db.execute(text("""
            SELECT ws.name, ws.code, wd.timestamp, wd.temperature, 
                   wd.humidity, wd.pressure, wd.weather_description
            FROM weather_data wd
            JOIN weather_stations ws ON wd.station_id = ws.id
            ORDER BY wd.timestamp DESC
            LIMIT 5
        """)).fetchall()
        
        for weather in recent_weather:
            timestamp = weather.timestamp.strftime("%Y-%m-%d %H:%M")
            print(f"   🌡️ {weather.name} ({weather.code}) - {timestamp}")
            print(f"      Temperature: {weather.temperature}°C | Humidity: {weather.humidity}%")
            print(f"      Pressure: {weather.pressure} hPa | {weather.weather_description}")
            print()
        
        # 4. Demonstrate spatial query (PostGIS)
        print("📍 SPATIAL QUERY DEMONSTRATION (PostGIS):")
        print("   Finding stations within 100km of Melbourne (-37.8136, 144.9631)")
        
        spatial_query = db.execute(text("""
            SELECT ws.name, ws.code, ws.state,
                   ST_Y(ws.location) as latitude, 
                   ST_X(ws.location) as longitude,
                   ST_Distance(
                       ST_Transform(ws.location, 3857),
                       ST_Transform(ST_GeomFromText('POINT(144.9631 -37.8136)', 4326), 3857)
                   ) / 1000 as distance_km
            FROM weather_stations ws
            WHERE ST_Distance(
                ST_Transform(ws.location, 3857),
                ST_Transform(ST_GeomFromText('POINT(144.9631 -37.8136)', 4326), 3857)
            ) <= 100000
            ORDER BY distance_km
        """)).fetchall()
        
        print(f"   ✅ Found {len(spatial_query)} stations within 100km:")
        for station in spatial_query:
            print(f"      📍 {station.name} ({station.code}) - {station.distance_km:.1f}km away")
        
        # 5. Show temperature statistics
        print(f"\n🌡️ TEMPERATURE ANALYSIS:")
        temp_stats = db.execute(text("""
            SELECT 
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(temperature) as avg_temp,
                COUNT(*) as total_readings
            FROM weather_data
            WHERE temperature IS NOT NULL
        """)).fetchone()
        
        print(f"   ❄️ Minimum Temperature: {temp_stats.min_temp}°C")
        print(f"   🔥 Maximum Temperature: {temp_stats.max_temp}°C")
        print(f"   📊 Average Temperature: {temp_stats.avg_temp:.1f}°C")
        print(f"   📈 Total Temperature Readings: {temp_stats.total_readings:,}")
        
        # 6. Show data distribution by state
        print(f"\n🗺️ DATA DISTRIBUTION BY STATE:")
        state_stats = db.execute(text("""
            SELECT ws.state, COUNT(wd.id) as reading_count, COUNT(DISTINCT ws.id) as station_count
            FROM weather_stations ws
            LEFT JOIN weather_data wd ON ws.id = wd.station_id
            GROUP BY ws.state
            ORDER BY reading_count DESC
        """)).fetchall()
        
        for state in state_stats:
            print(f"   🏛️ {state.state}: {state.station_count} stations, {state.reading_count:,} readings")
        
        # 7. Show PostGIS version
        print(f"\n🗄️ DATABASE TECHNICAL INFO:")
        postgis_version = db.execute(text("SELECT PostGIS_Version()")).fetchone()
        pg_version = db.execute(text("SELECT version()")).fetchone()
        
        print(f"   🔧 PostGIS Version: {postgis_version[0]}")
        print(f"   🐘 PostgreSQL: {pg_version[0].split(',')[0]}")
        
        print(f"\n✅ Database demonstration completed successfully!")
        print(f"🌐 Frontend available at: http://localhost:8000/")
        print(f"📖 API docs available at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import os
    
    # Set database URL if not already set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5433/weatherdb"
    
    asyncio.run(demonstrate_database())
