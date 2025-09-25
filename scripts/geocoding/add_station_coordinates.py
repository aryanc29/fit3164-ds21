"""
Script to add geographical coordinates to BOM weather stations
This will populate latitude/longitude data for the interactive map
"""

import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from bom_models import BOMWeatherStation
import requests
import time

# Create database connection
DATABASE_URL = "postgresql://postgres:password@localhost:5433/weatherdb"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Known NSW weather station coordinates (sample data)
# This is a curated list of major NSW weather stations with their coordinates
NSW_STATION_COORDINATES = {
    "ALBION PARK (SHELLHARBOUR AIRPORT)": (-34.5600, 150.7870),
    "ALBURY AIRPORT": (-36.0678, 146.9583),
    "ARMIDALE AIRPORT": (-30.5280, 151.6175),
    "BADGERYS CREEK": (-33.8830, 150.7470),
    "BANKSTOWN AIRPORT": (-33.9242, 150.9881),
    "BATHURST AIRPORT": (-33.4094, 149.6522),
    "BELLAMBI": (-34.3667, 150.9283),
    "BEGA": (-36.6833, 149.8333),
    "BROKEN HILL AIRPORT": (-32.0014, 141.4722),
    "CABRAMURRA": (-35.9333, 148.3833),
    "CAMDEN AIRPORT": (-34.0397, 150.6875),
    "CASINO AIRPORT": (-28.8797, 153.0525),
    "COBAR": (-31.4950, 145.8356),
    "COFFS HARBOUR": (-30.3167, 153.1167),
    "COOMA": (-36.2300, 149.1300),
    "DUBBO": (-32.2167, 148.5667),
    "GOULBURN": (-34.7500, 149.7167),
    "GRAFTON": (-29.6833, 152.9333),
    "GRIFFITH AIRPORT": (-34.2489, 146.0672),
    "HUNTER VALLEY": (-32.7833, 151.2167),
    "INVERELL": (-29.7833, 151.1333),
    "KEMPSEY": (-31.0833, 152.8333),
    "LISMORE": (-28.8167, 153.2833),
    "MOREE": (-29.5000, 149.8333),
    "MORUYA": (-35.9167, 150.1500),
    "MUDGEE": (-32.5667, 149.6000),
    "NARRABRI": (-30.3167, 149.7833),
    "NEWCASTLE": (-32.9167, 151.7833),
    "NOWRA": (-34.8833, 150.6000),
    "ORANGE": (-33.2833, 149.1000),
    "PARKES": (-33.1333, 148.2500),
    "PORT MACQUARIE": (-31.4333, 152.9000),
    "RICHMOND RAAF": (-33.6000, 150.7833),
    "SYDNEY AIRPORT": (-33.9461, 151.1772),
    "SYDNEY OBSERVATORY HILL": (-33.8588, 151.2056),
    "TAMWORTH": (-31.0833, 150.8500),
    "WAGGA WAGGA": (-35.1583, 147.4575),
    "WILLIAMTOWN": (-32.7889, 151.8431),
    "WOLLONGONG": (-34.4167, 150.9000),
    "YOUNG": (-34.3167, 148.3000)
}

def update_station_coordinates():
    """Update station coordinates in the database"""
    session = Session()
    
    try:
        # Get all stations from database
        stations = session.query(BOMWeatherStation).all()
        print(f"Found {len(stations)} stations in database")
        
        updated_count = 0
        
        for station in stations:
            station_name = station.station_name.upper().strip()
            
            # Check if we have coordinates for this station
            if station_name in NSW_STATION_COORDINATES:
                lat, lon = NSW_STATION_COORDINATES[station_name]
                
                # Update coordinates
                station.latitude = lat
                station.longitude = lon
                
                print(f"✅ Updated {station.station_name}: ({lat}, {lon})")
                updated_count += 1
            else:
                print(f"❌ No coordinates found for: {station.station_name}")
        
        # Commit changes
        session.commit()
        print(f"\n🎉 Successfully updated {updated_count} stations with coordinates")
        
        return updated_count
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating coordinates: {e}")
        return 0
    finally:
        session.close()

def add_additional_nsw_stations():
    """Add more NSW stations with approximate coordinates based on common station names"""
    
    # Additional stations with estimated coordinates
    additional_coordinates = {
        "BALLINA": (-28.8667, 153.5667),
        "BOURKE": (-30.0833, 145.9333),
        "CESSNOCK": (-32.8333, 151.3500),
        "CONDOBOLIN": (-33.0833, 147.1500),
        "COONABARABRAN": (-31.2833, 149.2667),
        "COONAMBLE": (-30.9833, 148.3833),
        "DENILIQUIN": (-35.5333, 144.9667),
        "FORBES": (-33.3833, 148.0167),
        "GLEN INNES": (-29.7333, 151.7333),
        "GUNNEDAH": (-30.9833, 150.2500),
        "HAY": (-34.5167, 144.8833),
        "LAKE CARGELLIGO": (-33.3000, 146.3667),
        "LIGHTNING RIDGE": (-29.4333, 147.9833),
        "MAITLAND": (-32.7333, 151.5667),
        "NYNGAN": (-31.5500, 147.2000),
        "SCONE": (-32.0500, 150.8667),
        "SINGLETON": (-32.5667, 151.1833),
        "TIBOOBURRA": (-29.4333, 142.0167),
        "TUMUT": (-35.3167, 148.2167),
        "WARREN": (-31.7000, 147.8333),
        "WEST WYALONG": (-33.9167, 147.2000),
        "WHITE CLIFFS": (-30.8500, 143.0833)
    }
    
    session = Session()
    
    try:
        updated_count = 0
        
        # Get all stations that still don't have coordinates
        stations_no_coords = session.query(BOMWeatherStation).filter(
            BOMWeatherStation.latitude.is_(None)
        ).all()
        
        print(f"\nChecking {len(stations_no_coords)} stations without coordinates...")
        
        for station in stations_no_coords:
            station_name = station.station_name.upper().strip()
            
            # Try to match with additional coordinates
            for key, (lat, lon) in additional_coordinates.items():
                if key in station_name:
                    station.latitude = lat
                    station.longitude = lon
                    print(f"✅ Updated {station.station_name}: ({lat}, {lon})")
                    updated_count += 1
                    break
        
        session.commit()
        print(f"🎉 Updated {updated_count} additional stations")
        
        return updated_count
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error adding additional coordinates: {e}")
        return 0
    finally:
        session.close()

def show_coordinate_summary():
    """Show summary of stations with/without coordinates"""
    session = Session()
    
    try:
        total_stations = session.query(BOMWeatherStation).count()
        stations_with_coords = session.query(BOMWeatherStation).filter(
            BOMWeatherStation.latitude.isnot(None),
            BOMWeatherStation.longitude.isnot(None)
        ).count()
        
        print(f"\n📊 COORDINATE SUMMARY:")
        print(f"Total stations: {total_stations}")
        print(f"Stations with coordinates: {stations_with_coords}")
        print(f"Stations without coordinates: {total_stations - stations_with_coords}")
        print(f"Coverage: {(stations_with_coords/total_stations)*100:.1f}%")
        
        # Show some examples
        stations_with_coords_sample = session.query(BOMWeatherStation).filter(
            BOMWeatherStation.latitude.isnot(None)
        ).limit(5).all()
        
        print(f"\n📍 Sample stations with coordinates:")
        for station in stations_with_coords_sample:
            print(f"  {station.station_name}: ({station.latitude:.4f}, {station.longitude:.4f})")
            
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Starting station coordinate update...")
    
    # Update with known coordinates
    updated1 = update_station_coordinates()
    
    # Add additional estimated coordinates
    updated2 = add_additional_nsw_stations()
    
    # Show summary
    show_coordinate_summary()
    
    print(f"\n✨ Coordinate update complete! Updated {updated1 + updated2} stations total.")
