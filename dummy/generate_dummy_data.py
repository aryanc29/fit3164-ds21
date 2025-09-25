#!/usr/bin/env python3
"""
Generfrom sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_GeomFromText
from app.database.connection import SessionLocal, engine
from app.api.models import WeatherStation, WeatherData, Base
import osmmy weather data for the weather visualization project
Creates realistic weather stations and weather data for testing
"""

# CODE REVIEW: dummy/generate_dummy_data.py - Realistic dummy data generation script
# GOOD PRACTICES:
# - Generates geographically accurate Australian weather stations
# - Uses seasonal temperature variations for realism
# - Includes comprehensive weather parameters (temp, humidity, pressure, wind, precipitation)
# - Uses PostGIS for spatial data storage
# - Includes data quality scores and weather codes
# - Handles duplicate data prevention
# - Provides detailed progress reporting
# - Uses proper database transactions and error handling
# - Includes realistic weather descriptions based on conditions
# - Generates time-series data with proper temporal distribution
# IMPROVEMENTS:
# - Could add more weather stations for better coverage
# - Could include historical weather patterns
# - Could add weather station metadata (equipment type, etc.)
# - Could include data anomalies for testing data quality algorithms
# - Could add configurable parameters for data generation
# - Could include weather alerts and warnings
# ARCHITECTURAL NOTES:
# - Creates test data that matches production schema
# - Enables development and testing without external data dependencies
# - Supports spatial analysis testing with PostGIS
# - Provides realistic data distribution for performance testing
# - Aligns with BOM data structure for integration testing

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_GeomFromText
from app.database.connection import SessionLocal, engine
from app.api.models import WeatherStation, WeatherData, Base
import os

# Australian cities with coordinates for realistic data
AUSTRALIAN_CITIES = [
    {"name": "Melbourne Central", "code": "MEL001", "lat": -37.8136, "lng": 144.9631, "state": "VIC", "elevation": 31},
    {"name": "Sydney Observatory", "code": "SYD001", "lat": -33.8688, "lng": 151.2093, "state": "NSW", "elevation": 39},
    {"name": "Brisbane Airport", "code": "BNE001", "lat": -27.4698, "lng": 153.0251, "state": "QLD", "elevation": 5},
    {"name": "Perth City", "code": "PER001", "lat": -31.9505, "lng": 115.8605, "state": "WA", "elevation": 20},
    {"name": "Adelaide CBD", "code": "ADL001", "lat": -34.9285, "lng": 138.6007, "state": "SA", "elevation": 50},
    {"name": "Hobart Waterfront", "code": "HOB001", "lat": -42.8821, "lng": 147.3272, "state": "TAS", "elevation": 4},
    {"name": "Darwin City", "code": "DAR001", "lat": -12.4634, "lng": 130.8456, "state": "NT", "elevation": 30},
    {"name": "Canberra Airport", "code": "CBR001", "lat": -35.3075, "lng": 149.1244, "state": "ACT", "elevation": 577},
    {"name": "Gold Coast", "code": "GLD001", "lat": -28.0167, "lng": 153.4000, "state": "QLD", "elevation": 10},
    {"name": "Newcastle", "code": "NEW001", "lat": -32.9283, "lng": 151.7817, "state": "NSW", "elevation": 12},
    {"name": "Wollongong", "code": "WOL001", "lat": -34.4278, "lng": 150.8931, "state": "NSW", "elevation": 3},
    {"name": "Geelong", "code": "GEE001", "lat": -38.1499, "lng": 144.3617, "state": "VIC", "elevation": 15},
    {"name": "Townsville", "code": "TSV001", "lat": -19.2590, "lng": 146.8169, "state": "QLD", "elevation": 15},
    {"name": "Cairns", "code": "CNS001", "lat": -16.9186, "lng": 145.7781, "state": "QLD", "elevation": 2},
    {"name": "Toowoomba", "code": "TWB001", "lat": -27.5598, "lng": 151.9507, "state": "QLD", "elevation": 691},
]

def generate_realistic_weather(station_name: str, date: datetime, season: str) -> dict:
    """Generate realistic weather data based on location and season"""
    
    # Base temperature ranges by city and season
    temp_ranges = {
        "Melbourne": {"summer": (15, 30), "autumn": (10, 22), "winter": (5, 16), "spring": (8, 20)},
        "Sydney": {"summer": (18, 32), "autumn": (12, 25), "winter": (8, 18), "spring": (12, 24)},
        "Brisbane": {"summer": (20, 35), "autumn": (15, 28), "winter": (10, 22), "spring": (15, 28)},
        "Perth": {"summer": (18, 35), "autumn": (12, 26), "winter": (8, 18), "spring": (10, 25)},
        "Adelaide": {"summer": (16, 32), "autumn": (12, 24), "winter": (7, 16), "spring": (10, 22)},
        "Hobart": {"summer": (12, 24), "autumn": (8, 18), "winter": (3, 12), "spring": (6, 16)},
        "Darwin": {"summer": (24, 35), "autumn": (22, 33), "winter": (18, 30), "spring": (22, 34)},
        "Canberra": {"summer": (12, 28), "autumn": (6, 20), "winter": (-2, 12), "spring": (4, 18)},
        "Gold Coast": {"summer": (20, 30), "autumn": (16, 26), "winter": (10, 21), "spring": (15, 25)},
        "Newcastle": {"summer": (18, 28), "autumn": (13, 23), "winter": (8, 17), "spring": (12, 22)},
        "Wollongong": {"summer": (17, 26), "autumn": (13, 22), "winter": (8, 16), "spring": (11, 20)},
        "Geelong": {"summer": (14, 26), "autumn": (9, 20), "winter": (5, 14), "spring": (7, 18)},
        "Townsville": {"summer": (23, 31), "autumn": (20, 29), "winter": (15, 26), "spring": (19, 29)},
        "Cairns": {"summer": (23, 31), "autumn": (20, 29), "winter": (17, 26), "spring": (20, 29)},
        "Toowoomba": {"summer": (16, 28), "autumn": (11, 23), "winter": (4, 16), "spring": (9, 22)},
    }
    
    # Get city name from station name
    city = station_name.split()[0]
    temp_range = temp_ranges.get(city, temp_ranges["Melbourne"])
    
    min_temp, max_temp = temp_range[season]
    temperature = round(random.uniform(min_temp, max_temp), 1)
    
    # Generate related weather parameters
    humidity = random.randint(30, 95)
    pressure = round(random.uniform(1005, 1025), 1)
    wind_speed = round(random.uniform(0, 25), 1)
    wind_direction = random.randint(0, 360)
    
    # Precipitation based on season and location
    precip_chance = {"summer": 0.2, "autumn": 0.3, "winter": 0.4, "spring": 0.3}
    precipitation = round(random.uniform(0, 15), 1) if random.random() < precip_chance[season] else 0.0
    
    visibility = round(random.uniform(5, 20), 1)
    
    # Weather descriptions based on conditions
    if precipitation > 10:
        weather_desc = "Heavy Rain"
        weather_code = "HR"
    elif precipitation > 2:
        weather_desc = "Light Rain"
        weather_code = "LR"
    elif humidity > 80:
        weather_desc = "Cloudy"
        weather_code = "CL"
    elif temperature > max_temp * 0.8:
        weather_desc = "Sunny"
        weather_code = "SU"
    else:
        weather_desc = "Partly Cloudy"
        weather_code = "PC"
    
    return {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "precipitation": precipitation,
        "visibility": visibility,
        "weather_code": weather_code,
        "weather_description": weather_desc,
        "quality_score": round(random.uniform(0.8, 1.0), 2)
    }

def get_season(date: datetime) -> str:
    """Get Australian season for a given date"""
    month = date.month
    if month in [12, 1, 2]:
        return "summer"
    elif month in [3, 4, 5]:
        return "autumn"
    elif month in [6, 7, 8]:
        return "winter"
    else:
        return "spring"

def create_weather_stations(db: Session):
    """Create weather stations from Australian cities"""
    print("🏗️ Creating weather stations...")
    
    stations_created = 0
    for city_data in AUSTRALIAN_CITIES:
        # Check if station already exists
        existing = db.query(WeatherStation).filter(WeatherStation.code == city_data["code"]).first()
        if existing:
            print(f"   Station {city_data['code']} already exists, skipping...")
            continue
            
        station = WeatherStation(
            name=city_data["name"],
            code=city_data["code"],
            country="Australia",
            state=city_data["state"],
            elevation=city_data["elevation"],
            location=ST_GeomFromText(f"POINT({city_data['lng']} {city_data['lat']})", 4326),
            is_active=True,
            data_source="BOM",
            created_at=datetime.utcnow()
        )
        
        db.add(station)
        stations_created += 1
        
    db.commit()
    print(f"✅ Created {stations_created} weather stations")
    return db.query(WeatherStation).all()

def create_weather_data(db: Session, stations: list, days_back: int = 30):
    """Create weather data for all stations"""
    print(f"🌡️ Generating weather data for last {days_back} days...")
    
    # Generate data for each day
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    data_points_created = 0
    
    for station in stations:
        current_date = start_date
        
        while current_date <= end_date:
            # Generate 4 readings per day (every 6 hours)
            for hour in [0, 6, 12, 18]:
                timestamp = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Check if data already exists
                existing = db.query(WeatherData).filter(
                    WeatherData.station_id == station.id,
                    WeatherData.timestamp == timestamp
                ).first()
                
                if existing:
                    continue
                
                season = get_season(current_date)
                weather_data = generate_realistic_weather(station.name, current_date, season)
                
                weather_record = WeatherData(
                    station_id=station.id,
                    timestamp=timestamp,
                    temperature=weather_data["temperature"],
                    humidity=weather_data["humidity"],
                    pressure=weather_data["pressure"],
                    wind_speed=weather_data["wind_speed"],
                    wind_direction=weather_data["wind_direction"],
                    precipitation=weather_data["precipitation"],
                    visibility=weather_data["visibility"],
                    weather_code=weather_data["weather_code"],
                    weather_description=weather_data["weather_description"],
                    data_source="BOM",
                    quality_score=weather_data["quality_score"],
                    created_at=datetime.utcnow()
                )
                
                db.add(weather_record)
                data_points_created += 1
                
            current_date += timedelta(days=1)
        
        # Commit after each station to avoid large transactions
        db.commit()
        print(f"   ✅ Generated data for {station.name} ({station.code})")
    
    print(f"✅ Created {data_points_created} weather data points")

def generate_summary_stats(db: Session):
    """Generate summary statistics of the created data"""
    print("\n📊 Data Summary:")
    
    # Station count
    station_count = db.query(WeatherStation).count()
    print(f"   🏢 Weather Stations: {station_count}")
    
    # Weather data count
    data_count = db.query(WeatherData).count()
    print(f"   📈 Weather Records: {data_count}")
    
    # Date range
    min_date = db.query(func.min(WeatherData.timestamp)).scalar()
    max_date = db.query(func.max(WeatherData.timestamp)).scalar()
    print(f"   📅 Date Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    
    # Temperature range
    min_temp = db.query(func.min(WeatherData.temperature)).scalar()
    max_temp = db.query(func.max(WeatherData.temperature)).scalar()
    avg_temp = db.query(func.avg(WeatherData.temperature)).scalar()
    print(f"   🌡️ Temperature Range: {min_temp}°C to {max_temp}°C (avg: {avg_temp:.1f}°C)")
    
    # Sample recent data
    print(f"\n📋 Recent Weather Data Sample:")
    recent_data = db.query(WeatherData).join(WeatherStation).order_by(WeatherData.timestamp.desc()).limit(5).all()
    
    for record in recent_data:
        print(f"   • {record.station.name}: {record.temperature}°C, {record.weather_description} ({record.timestamp.strftime('%Y-%m-%d %H:%M')})")

def main():
    """Main function to generate all dummy data"""
    print("🚀 Generating dummy weather data...")
    print("="*60)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Step 0: Ensure tables exist
        print("📋 Creating database tables if they don't exist...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ready")
        
        # Step 1: Create weather stations
        stations = create_weather_stations(db)
        
        # Step 2: Generate weather data
        create_weather_data(db, stations, days_back=30)
        
        # Step 3: Generate summary
        generate_summary_stats(db)
        
        print("\n🎉 Dummy data generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error generating dummy data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
