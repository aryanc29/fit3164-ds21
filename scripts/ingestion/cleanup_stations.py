"""
Clean up bom_weather_stations to contain exactly the same 518 stations as bom_weather_data.
This removes stations that don't have weather data and ensures perfect 1:1 matching.
"""
import psycopg2

def cleanup_stations():
    """Keep only stations that exist in bom_weather_data"""
    conn = psycopg2.connect("postgresql://postgres:password@localhost:5433/weatherdb")
    cur = conn.cursor()
    
    try:
        print("🧹 Starting cleanup of bom_weather_stations...")
        
        # First, get current counts
        cur.execute("SELECT COUNT(*) FROM bom_weather_stations")
        before_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT station_name) FROM bom_weather_data")
        target_count = cur.fetchone()[0]
        
        print(f"📊 Current stations: {before_count}")
        print(f"🎯 Target stations: {target_count}")
        
        # Remove stations that don't exist in bom_weather_data
        delete_sql = """
        DELETE FROM bom_weather_stations 
        WHERE station_name NOT IN (
            SELECT DISTINCT station_name FROM bom_weather_data
        );
        """
        
        cur.execute(delete_sql)
        deleted_count = cur.rowcount
        
        # Verify final count
        cur.execute("SELECT COUNT(*) FROM bom_weather_stations")
        after_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM bom_weather_stations WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        with_coords = cur.fetchone()[0]
        
        conn.commit()
        
        print(f"✅ Cleanup completed!")
        print(f"🗑️  Removed {deleted_count} stations")
        print(f"📍 Final count: {after_count} stations")
        print(f"🗺️  With coordinates: {with_coords}")
        print(f"❓ Without coordinates: {after_count - with_coords}")
        
        if after_count == target_count:
            print("🎉 Perfect match! bom_weather_stations now has exactly 518 stations")
        else:
            print(f"⚠️  Mismatch: Expected {target_count}, got {after_count}")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during cleanup: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    cleanup_stations()