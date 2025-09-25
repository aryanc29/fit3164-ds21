#!/usr/bin/env python3
"""
Check geocoded weather stations in the database
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_geocoded_stations():
    """Check which stations have coordinates in the database"""
    
    # Database connection
    database_url = "postgresql+pg8000://postgres:password@localhost:5433/weatherdb"
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Checking geocoded stations in the database...")
        print("=" * 60)
        
        # First check the table structure
        structure_query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'weather_stations'
            ORDER BY ordinal_position
        """)
        
        structure_result = session.execute(structure_query)
        columns = structure_result.fetchall()
        
        print("Table structure:")
        for col in columns:
            print(f"  {col.column_name}: {col.data_type}")
        print()
        
        # Query stations with coordinates (using correct column names)
        query = text("""
            SELECT 
                id,
                name,
                ST_X(location::geometry) as longitude,
                ST_Y(location::geometry) as latitude,
                location IS NOT NULL as has_location
            FROM weather_stations 
            WHERE location IS NOT NULL
            ORDER BY id
            LIMIT 20
        """)
        
        result = session.execute(query)
        stations = result.fetchall()
        
        if stations:
            print(f"Found {len(stations)} stations with coordinates:")
            print()
            for station in stations:
                print(f"ID: {station.id:3d} | {station.name:40s} | Lat: {station.latitude:9.6f} | Lon: {station.longitude:9.6f}")
        else:
            print("No stations with coordinates found!")
            
        # Count total stations vs geocoded
        count_query = text("""
            SELECT 
                COUNT(*) as total_stations,
                COUNT(location) as geocoded_stations,
                COUNT(*) - COUNT(location) as missing_coordinates
            FROM weather_stations
        """)
        
        count_result = session.execute(count_query)
        counts = count_result.fetchone()
        
        print()
        print("=" * 60)
        print(f"Total stations: {counts.total_stations}")
        print(f"Geocoded stations: {counts.geocoded_stations}")
        print(f"Missing coordinates: {counts.missing_coordinates}")
        
        session.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False
        
    return True

if __name__ == "__main__":
    check_geocoded_stations()