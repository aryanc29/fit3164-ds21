#!/usr/bin/env python3
"""
Verify and display the generated dummy data
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from database import SessionLocal
from models import WeatherStation, WeatherData
import json

def display_weather_stations(db: Session):
    """Display all weather stations"""
    print("🏢 Weather Stations:")
    print("-" * 80)
    
    stations = db.query(WeatherStation).order_by(WeatherStation.name).all()
    
    for station in stations:
        # Get location coordinates
        result = db.execute(text("""
            SELECT ST_X(location) as lng, ST_Y(location) as lat 
            FROM weather_stations 
            WHERE id = :station_id
        """), {"station_id": station.id})
        coords = result.fetchone()
        
        print(f"   {station.code}: {station.name}")
        print(f"      Location: {coords.lat:.4f}, {coords.lng:.4f} ({station.state})")
        print(f"      Elevation: {station.elevation}m | Source: {station.data_source}")
        print()

def display_recent_weather(db: Session, limit: int = 20):
    """Display recent weather data"""
    print(f"🌡️ Recent Weather Data (last {limit} records):")
    print("-" * 100)
    
    recent_data = (db.query(WeatherData)
                   .join(WeatherStation)
                   .order_by(WeatherData.timestamp.desc())
                   .limit(limit)
                   .all())
    
    for record in recent_data:
        print(f"   {record.timestamp.strftime('%Y-%m-%d %H:%M')} | "
              f"{record.station.code} ({record.station.name[:20]:20}) | "
              f"{record.temperature:5.1f}°C | {record.humidity:3.0f}% | "
              f"{record.weather_description:12} | {record.precipitation:4.1f}mm")

def display_statistics(db: Session):
    """Display data statistics"""
    print("📊 Weather Data Statistics:")
    print("-" * 50)
    
    # Temperature statistics
    temp_stats = db.query(
        func.min(WeatherData.temperature).label('min_temp'),
        func.max(WeatherData.temperature).label('max_temp'),
        func.avg(WeatherData.temperature).label('avg_temp')
    ).first()
    
    print(f"   Temperature: {temp_stats.min_temp}°C to {temp_stats.max_temp}°C (avg: {temp_stats.avg_temp:.1f}°C)")
    
    # Humidity statistics
    humidity_stats = db.query(
        func.min(WeatherData.humidity).label('min_humidity'),
        func.max(WeatherData.humidity).label('max_humidity'),
        func.avg(WeatherData.humidity).label('avg_humidity')
    ).first()
    
    print(f"   Humidity: {humidity_stats.min_humidity}% to {humidity_stats.max_humidity}% (avg: {humidity_stats.avg_humidity:.1f}%)")
    
    # Precipitation statistics
    precip_stats = db.query(
        func.min(WeatherData.precipitation).label('min_precip'),
        func.max(WeatherData.precipitation).label('max_precip'),
        func.avg(WeatherData.precipitation).label('avg_precip')
    ).first()
    
    print(f"   Precipitation: {precip_stats.min_precip}mm to {precip_stats.max_precip}mm (avg: {precip_stats.avg_precip:.2f}mm)")
    
    # Data by station
    print("\n   Records per station:")
    station_counts = (db.query(WeatherStation.code, WeatherStation.name, func.count(WeatherData.id).label('count'))
                      .join(WeatherData)
                      .group_by(WeatherStation.id, WeatherStation.code, WeatherStation.name)
                      .order_by(WeatherStation.code)
                      .all())
    
    for station_code, station_name, count in station_counts:
        print(f"      {station_code}: {count} records")

def test_spatial_queries(db: Session):
    """Test some spatial queries"""
    print("🗺️ Spatial Query Examples:")
    print("-" * 50)
    
    # Find stations within 100km of Melbourne
    print("   Weather stations within 100km of Melbourne:")
    melbourne_nearby = db.execute(text("""
        SELECT s.code, s.name, 
               ST_Distance(
                   ST_Transform(s.location, 3857),
                   ST_Transform(ST_GeomFromText('POINT(144.9631 -37.8136)', 4326), 3857)
               ) / 1000 as distance_km
        FROM weather_stations s
        WHERE ST_Distance(
            ST_Transform(s.location, 3857),
            ST_Transform(ST_GeomFromText('POINT(144.9631 -37.8136)', 4326), 3857)
        ) <= 100000
        ORDER BY distance_km;
    """))
    
    for row in melbourne_nearby:
        print(f"      {row.code}: {row.name} ({row.distance_km:.1f} km)")
    
    # Find the hottest temperature recorded
    print("\n   Hottest temperature recorded:")
    hottest = (db.query(WeatherData, WeatherStation)
               .join(WeatherStation)
               .order_by(WeatherData.temperature.desc())
               .first())
    
    if hottest:
        data, station = hottest
        print(f"      {data.temperature}°C at {station.name} on {data.timestamp.strftime('%Y-%m-%d %H:%M')}")

def export_sample_data(db: Session):
    """Export sample data to JSON"""
    print("💾 Exporting sample data...")
    
    # Get sample of stations
    stations = db.query(WeatherStation).limit(3).all()
    sample_data = []
    
    for station in stations:
        # Get coordinates
        coords_result = db.execute(text("""
            SELECT ST_X(location) as lng, ST_Y(location) as lat 
            FROM weather_stations 
            WHERE id = :station_id
        """), {"station_id": station.id})
        coords = coords_result.fetchone()
        
        # Get recent weather data
        recent_weather = (db.query(WeatherData)
                         .filter(WeatherData.station_id == station.id)
                         .order_by(WeatherData.timestamp.desc())
                         .limit(5)
                         .all())
        
        weather_records = []
        for record in recent_weather:
            weather_records.append({
                "timestamp": record.timestamp.isoformat(),
                "temperature": record.temperature,
                "humidity": record.humidity,
                "pressure": record.pressure,
                "weather_description": record.weather_description,
                "precipitation": record.precipitation
            })
        
        station_data = {
            "station_id": station.id,
            "code": station.code,
            "name": station.name,
            "location": {
                "latitude": coords.lat,
                "longitude": coords.lng
            },
            "elevation": station.elevation,
            "state": station.state,
            "recent_weather": weather_records
        }
        sample_data.append(station_data)
    
    # Save to file
    with open("sample_weather_data.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"   ✅ Sample data exported to sample_weather_data.json")

def main():
    """Main verification function"""
    print("🔍 Weather Data Verification Report")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Display basic information
        display_weather_stations(db)
        display_statistics(db)
        display_recent_weather(db, limit=15)
        test_spatial_queries(db)
        export_sample_data(db)
        
        print("\n✅ Data verification completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
