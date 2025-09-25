#!/usr/bin/env python3
"""
Extract weather stations from bom_weather_data and populate bom_weather_stations table
This replaces the previous approach and focuses on the BOM stations table.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def extract_bom_stations():
    """Extract unique station names from bom_weather_data and populate bom_weather_stations"""
    
    # Database connection
    database_url = "postgresql+pg8000://postgres:password@localhost:5433/weatherdb"
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Starting BOM weather stations extraction...")
        print("=" * 60)
        
        # First, clear existing data in bom_weather_stations (if you want fresh start)
        print("Checking current bom_weather_stations content...")
        current_count = session.execute(text("SELECT COUNT(*) FROM bom_weather_stations")).scalar()
        print(f"Current bom_weather_stations records: {current_count}")
        
        response = input("Do you want to clear existing bom_weather_stations and start fresh? (y/N): ")
        if response.lower() == 'y':
            print("Clearing existing bom_weather_stations...")
            session.execute(text("DELETE FROM bom_weather_stations"))
            session.commit()
            print("✅ Cleared existing records")
        
        # Extract unique stations from bom_weather_data
        print("\nExtracting unique stations from bom_weather_data...")
        
        extract_query = text("""
            SELECT DISTINCT
                station_name
            FROM bom_weather_data
            WHERE station_name IS NOT NULL 
            AND station_name != ''
            ORDER BY station_name
        """)
        
        result = session.execute(extract_query)
        unique_stations = result.fetchall()
        
        print(f"Found {len(unique_stations)} unique stations in bom_weather_data")
        
        if len(unique_stations) == 0:
            print("❌ No stations found in bom_weather_data table!")
            return False
            
        # Show sample of what we found
        print("\nSample stations to be inserted:")
        for i, station in enumerate(unique_stations[:5]):
            print(f"  {i+1}. {station.station_name}")
        
        if len(unique_stations) > 5:
            print(f"  ... and {len(unique_stations) - 5} more stations")
            
        # Insert stations into bom_weather_stations
        print(f"\nInserting {len(unique_stations)} stations into bom_weather_stations...")
        
        inserted_count = 0
        skipped_count = 0
        
        for station in unique_stations:
            try:
                # Check if station already exists (by station_name)
                check_query = text("""
                    SELECT COUNT(*) FROM bom_weather_stations 
                    WHERE station_name = :name
                """)
                
                existing = session.execute(check_query, {
                    'name': station.station_name
                }).scalar()
                
                if existing > 0:
                    skipped_count += 1
                    continue
                
                # Generate station code from name
                station_code = f"BOM_{station.station_name.upper().replace(' ', '_').replace('(', '').replace(')', '').replace('_', '_')}"
                
                # Insert new station (without coordinates - will be geocoded later)
                insert_query = text("""
                    INSERT INTO bom_weather_stations 
                    (station_name, station_code, state, country, latitude, longitude, is_active, data_source, created_at, updated_at)
                    VALUES 
                    (:name, :code, :state, 'Australia', NULL, NULL, true, 'BOM', :created, :updated)
                """)
                
                session.execute(insert_query, {
                    'name': station.station_name,
                    'code': station_code,
                    'state': 'NSW',  # Default to NSW - will be corrected during geocoding
                    'created': datetime.now(),
                    'updated': datetime.now()
                })
                
                inserted_count += 1
                
                if inserted_count % 50 == 0:
                    print(f"  Inserted {inserted_count} stations...")
                    
            except Exception as e:
                print(f"❌ Error inserting station {station.station_name}: {e}")
                continue
        
        # Commit all changes
        session.commit()
        
        print("\n" + "=" * 60)
        print("BOM STATIONS EXTRACTION COMPLETED")
        print("=" * 60)
        print(f"✅ Inserted: {inserted_count} new stations")
        print(f"⏭️  Skipped: {skipped_count} existing stations")
        
        # Final verification
        final_count = session.execute(text("SELECT COUNT(*) FROM bom_weather_stations")).scalar()
        with_coords = session.execute(text("SELECT COUNT(*) FROM bom_weather_stations WHERE latitude IS NOT NULL AND longitude IS NOT NULL")).scalar()
        without_coords = final_count - with_coords
        
        print(f"📊 Total BOM stations: {final_count}")
        print(f"🗺️  With coordinates: {with_coords}")
        print(f"❓ Missing coordinates: {without_coords}")
        
        if without_coords > 0:
            print(f"\n🔄 Next step: Run geocoding on {without_coords} stations missing coordinates")
        else:
            print("\n✅ All stations have coordinates!")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return False

if __name__ == "__main__":
    print("BOM Weather Stations Extraction Script")
    print("This will populate the bom_weather_stations table from bom_weather_data")
    print()
    
    success = extract_bom_stations()
    
    if success:
        print("\n🎉 Extraction completed successfully!")
        print("You can now run geocoding on stations missing coordinates.")
    else:
        print("\n❌ Extraction failed. Please check the errors above.")