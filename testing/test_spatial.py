#!/usr/bin/env python3
"""
Test script to verify PostGIS spatial functionality
"""

from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry
from shapely.geometry import Point
import os

def test_spatial_functions():
    """Test PostGIS spatial functions"""
    
    # Database connection
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://weather_user:weather_pass@localhost:5433/weather_db"
    )
    
    engine = create_engine(DATABASE_URL)
    
    print("🧪 Testing PostGIS spatial functions...")
    
    with engine.connect() as connection:
        
        # Test 1: PostGIS version
        result = connection.execute(text("SELECT PostGIS_Version();"))
        version = result.fetchone()
        print(f"✅ PostGIS Version: {version[0]}")
        
        # Test 2: Create a point geometry
        result = connection.execute(text("""
            SELECT ST_AsText(ST_GeomFromText('POINT(144.9631 -37.8136)', 4326)) as melbourne_point;
        """))
        point = result.fetchone()
        print(f"✅ Melbourne Point: {point[0]}")
        
        # Test 3: Calculate distance (Melbourne to Sydney)
        result = connection.execute(text("""
            SELECT ST_Distance(
                ST_GeomFromText('POINT(144.9631 -37.8136)', 4326), -- Melbourne
                ST_GeomFromText('POINT(151.2093 -33.8688)', 4326)   -- Sydney
            ) as distance_degrees;
        """))
        distance = result.fetchone()
        print(f"✅ Distance Melbourne to Sydney: {distance[0]:.4f} degrees")
        
        # Test 4: Calculate actual distance in meters
        result = connection.execute(text("""
            SELECT ST_Distance(
                ST_Transform(ST_GeomFromText('POINT(144.9631 -37.8136)', 4326), 3857),
                ST_Transform(ST_GeomFromText('POINT(151.2093 -33.8688)', 4326), 3857)
            ) as distance_meters;
        """))
        distance_m = result.fetchone()
        print(f"✅ Distance Melbourne to Sydney: {distance_m[0]/1000:.2f} km")
        
        # Test 5: Check available spatial reference systems
        result = connection.execute(text("""
            SELECT COUNT(*) as srid_count FROM spatial_ref_sys;
        """))
        srid_count = result.fetchone()
        print(f"✅ Available coordinate systems: {srid_count[0]}")
        
        # Test 6: Test buffer operation
        result = connection.execute(text("""
            SELECT ST_AsText(ST_Buffer(
                ST_GeomFromText('POINT(144.9631 -37.8136)', 4326),
                0.01
            )) as buffer_geom;
        """))
        buffer_geom = result.fetchone()
        print(f"✅ Buffer around Melbourne: Created polygon")
        
    print("🎉 All spatial tests passed!")

if __name__ == "__main__":
    test_spatial_functions()
