#!/usr/bin/env python3
"""
Extract unique weather station names from weather data table
and populate the weather_stations table before geocoding
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine
from sqlalchemy import text

def check_data_structure():
    """Check what tables and data we have"""
    with engine.connect() as conn:
        # Check what tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        
        print("Available tables:")
        tables = []
        for row in result:
            tables.append(row[0])
            print(f"  - {row[0]}")
        
        # Check weather data tables for station names
        for table in ['weather_data', 'bom_weather_data']:
            if table in tables:
                print(f"\nChecking {table} table:")
                
                # Get column names
                result = conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position;
                """))
                
                columns = []
                for row in result:
                    columns.append(row[0])
                    print(f"  - {row[0]} ({row[1]})")
                
                # Count records
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = result.scalar()
                print(f"  Total records: {count}")
                
                # Check for station name variations
                station_columns = [col for col in columns if 'station' in col.lower()]
                if station_columns:
                    print(f"  Station-related columns: {station_columns}")
                    
                    # Sample some station names
                    for col in station_columns[:3]:  # Check first 3 station columns
                        result = conn.execute(text(f"""
                            SELECT DISTINCT {col} 
                            FROM {table} 
                            WHERE {col} IS NOT NULL 
                            LIMIT 5;
                        """))
                        
                        print(f"  Sample {col} values:")
                        for row in result:
                            print(f"    - {row[0]}")

if __name__ == "__main__":
    check_data_structure()