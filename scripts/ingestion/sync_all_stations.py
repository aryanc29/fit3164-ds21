"""
Sync all stations from bom_weather_data to bom_weather_stations table.
This ensures bom_weather_stations always has 518 stations (same as bom_weather_data),
including those without coordinates.
"""
import psycopg2
import os

def get_db_connection():
    """Get database connection using docker-compose credentials"""
    return psycopg2.connect(
        db_url="postgresql://postgres:password@localhost:5433/weatherdb"
    )

def sync_stations():
    """Insert missing stations from bom_weather_data into bom_weather_stations"""
    conn = psycopg2.connect("postgresql://postgres:password@localhost:5433/weatherdb")
    cur = conn.cursor()
    
    try:
        # Insert stations that exist in bom_weather_data but not in bom_weather_stations
        insert_sql = """
        INSERT INTO bom_weather_stations (station_name, latitude, longitude, created_at, updated_at)
        SELECT DISTINCT 
            bwd.station_name,
            NULL::DOUBLE PRECISION as latitude,
            NULL::DOUBLE PRECISION as longitude,
            NOW() as created_at,
            NOW() as updated_at
        FROM bom_weather_data bwd
        WHERE bwd.station_name NOT IN (
            SELECT station_name FROM bom_weather_stations
        );
        """
        
        cur.execute(insert_sql)
        rows_inserted = cur.rowcount
        
        # Get final counts
        cur.execute("SELECT COUNT(*) FROM bom_weather_stations")
        total_stations = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM bom_weather_stations WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        stations_with_coords = cur.fetchone()[0]
        
        conn.commit()
        
        print(f"✅ Successfully synced stations!")
        print(f"📊 Inserted {rows_inserted} new stations without coordinates")
        print(f"📍 Total stations: {total_stations}")
        print(f"🗺️  Stations with coordinates: {stations_with_coords}")
        print(f"❓ Stations without coordinates: {total_stations - stations_with_coords}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during sync: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    sync_stations()