#!/usr/bin/env python3
"""
Check bom_weather_stations table for missing coordinates
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_bom_stations():
    """Check which BOM stations are missing coordinates"""
    
    database_url = "postgresql+pg8000://postgres:password@localhost:5433/weatherdb"
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Checking BOM weather stations for missing coordinates...")
        print("=" * 60)
        
        # Count stations with and without coordinates
        count_query = text("""
            SELECT 
                COUNT(*) as total_stations,
                COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) as with_coordinates,
                COUNT(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1 END) as missing_coordinates
            FROM bom_weather_stations
        """)
        
        count_result = session.execute(count_query)
        counts = count_result.fetchone()
        
        print(f"Total BOM stations: {counts.total_stations}")
        print(f"With coordinates: {counts.with_coordinates}")
        print(f"Missing coordinates: {counts.missing_coordinates}")
        print()
        
        # Show stations missing coordinates
        if counts.missing_coordinates > 0:
            print("Stations missing coordinates:")
            missing_query = text("""
                SELECT id, station_name, station_code, state, latitude, longitude
                FROM bom_weather_stations 
                WHERE latitude IS NULL OR longitude IS NULL
                ORDER BY station_name
                LIMIT 10
            """)
            
            missing_result = session.execute(missing_query)
            missing_stations = missing_result.fetchall()
            
            for station in missing_stations:
                print(f"ID: {station.id:3d} | {station.station_name:40s} | {station.state} | Lat: {station.latitude} | Lon: {station.longitude}")
        else:
            print("All BOM stations have coordinates! ✅")
            
        # Sample of stations with coordinates
        print("\nSample stations with coordinates:")
        sample_query = text("""
            SELECT id, station_name, state, latitude, longitude
            FROM bom_weather_stations 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY station_name
            LIMIT 5
        """)
        
        sample_result = session.execute(sample_query)
        sample_stations = sample_result.fetchall()
        
        for station in sample_stations:
            print(f"ID: {station.id:3d} | {station.station_name:40s} | {station.state} | Lat: {station.latitude:9.6f} | Lon: {station.longitude:9.6f}")
        
        session.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False
        
    return True

if __name__ == "__main__":
    check_bom_stations()