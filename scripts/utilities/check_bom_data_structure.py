#!/usr/bin/env python3
"""
Check the structure of bom_weather_data table to understand available columns
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_bom_weather_data_structure():
    """Check the structure of bom_weather_data table"""
    
    database_url = "postgresql+pg8000://postgres:password@localhost:5433/weatherdb"
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Checking bom_weather_data table structure...")
        print("=" * 60)
        
        # Check table structure
        structure_query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'bom_weather_data'
            ORDER BY ordinal_position
        """)
        
        structure_result = session.execute(structure_query)
        columns = structure_result.fetchall()
        
        print("Available columns:")
        for col in columns:
            print(f"  {col.column_name:25s} | {col.data_type:15s} | Nullable: {col.is_nullable}")
        
        # Sample data
        print("\nSample data (first 2 rows):")
        sample_query = text("SELECT * FROM bom_weather_data LIMIT 2")
        sample_result = session.execute(sample_query)
        samples = sample_result.fetchall()
        
        if samples:
            # Get column names for headers
            column_names = [col.column_name for col in columns]
            print("  " + " | ".join(column_names[:10]))  # Show first 10 columns
            print("  " + "-" * 120)
            
            for sample in samples:
                # Show first 10 values
                values = [str(val)[:15] if val is not None else "NULL" for val in sample[:10]]
                print("  " + " | ".join(values))
        
        # Check unique station names
        print(f"\nUnique station analysis:")
        unique_stations_query = text("""
            SELECT COUNT(DISTINCT station_name) as unique_stations,
                   COUNT(*) as total_records
            FROM bom_weather_data
            WHERE station_name IS NOT NULL
        """)
        
        unique_result = session.execute(unique_stations_query)
        unique_data = unique_result.fetchone()
        
        print(f"  Unique station names: {unique_data.unique_stations}")
        print(f"  Total records: {unique_data.total_records}")
        
        # Show sample station names
        print(f"\nSample station names:")
        sample_stations_query = text("""
            SELECT DISTINCT station_name
            FROM bom_weather_data
            WHERE station_name IS NOT NULL
            ORDER BY station_name
            LIMIT 10
        """)
        
        sample_stations_result = session.execute(sample_stations_query)
        sample_stations = sample_stations_result.fetchall()
        
        for i, station in enumerate(sample_stations, 1):
            print(f"  {i:2d}. {station.station_name}")
        
        session.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False
        
    return True

if __name__ == "__main__":
    check_bom_weather_data_structure()