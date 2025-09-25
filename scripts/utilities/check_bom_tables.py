#!/usr/bin/env python3
"""
Check the structure of bom_weather_stations vs weather_stations tables
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_table_structures():
    """Compare the structure of bom_weather_stations and weather_stations tables"""
    
    # Database connection
    database_url = "postgresql+pg8000://postgres:password@localhost:5433/weatherdb"
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Checking table structures...")
        print("=" * 80)
        
        # Check bom_weather_stations structure
        print("BOM_WEATHER_STATIONS TABLE STRUCTURE:")
        bom_structure_query = text("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'bom_weather_stations'
            ORDER BY ordinal_position
        """)
        
        bom_result = session.execute(bom_structure_query)
        bom_columns = bom_result.fetchall()
        
        if bom_columns:
            for col in bom_columns:
                print(f"  {col.column_name:20s} | {col.data_type:15s} | Nullable: {col.is_nullable} | Default: {col.column_default}")
            
            # Check sample data
            print("\nSample data from bom_weather_stations:")
            sample_query = text("SELECT * FROM bom_weather_stations LIMIT 3")
            sample_result = session.execute(sample_query)
            samples = sample_result.fetchall()
            
            if samples:
                # Print column headers
                print("  " + " | ".join([col.column_name for col in bom_columns]))
                print("  " + "-" * 100)
                for sample in samples:
                    print("  " + " | ".join([str(val)[:15] if val is not None else "NULL" for val in sample]))
        else:
            print("  Table not found or no columns!")
            
        print("\n" + "=" * 80)
        print("WEATHER_STATIONS TABLE STRUCTURE:")
        
        # Check weather_stations structure
        ws_structure_query = text("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'weather_stations'
            ORDER BY ordinal_position
        """)
        
        ws_result = session.execute(ws_structure_query)
        ws_columns = ws_result.fetchall()
        
        for col in ws_columns:
            print(f"  {col.column_name:20s} | {col.data_type:15s} | Nullable: {col.is_nullable} | Default: {col.column_default}")
            
        # Check counts
        print("\n" + "=" * 80)
        print("RECORD COUNTS:")
        
        count_bom = session.execute(text("SELECT COUNT(*) FROM bom_weather_stations")).scalar()
        count_ws = session.execute(text("SELECT COUNT(*) FROM weather_stations")).scalar()
        count_ws_with_coords = session.execute(text("SELECT COUNT(*) FROM weather_stations WHERE location IS NOT NULL")).scalar()
        
        print(f"  bom_weather_stations: {count_bom}")
        print(f"  weather_stations: {count_ws}")
        print(f"  weather_stations (with coordinates): {count_ws_with_coords}")
        
        session.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False
        
    return True

if __name__ == "__main__":
    check_table_structures()