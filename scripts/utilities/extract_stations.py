#!/usr/bin/env python3
"""
Extract unique station names from bom_weather_data table
and populate the weather_stations table with proper geocoding preparation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_and_populate_stations(dry_run=False):
    """Extract unique station names from bom_weather_data and populate weather_stations"""
    
    with engine.connect() as conn:
        # First, check what unique station names we have
        logger.info("Extracting unique station names from bom_weather_data...")
        
        result = conn.execute(text("""
            SELECT DISTINCT station_name, COUNT(*) as record_count
            FROM bom_weather_data
            WHERE station_name IS NOT NULL
            GROUP BY station_name
            ORDER BY station_name;
        """))
        
        unique_stations = []
        total_records = 0
        
        for row in result:
            station_name = row[0]
            record_count = row[1]
            unique_stations.append({
                'name': station_name,
                'record_count': record_count
            })
            total_records += record_count
        
        logger.info(f"Found {len(unique_stations)} unique station names")
        logger.info(f"Total weather records: {total_records}")
        
        # Show sample stations
        logger.info("Sample stations:")
        for station in unique_stations[:10]:
            logger.info(f"  - {station['name']} ({station['record_count']} records)")
        
        if dry_run:
            logger.info("[DRY RUN] Would populate weather_stations table with these stations")
            return
        
        # Check which stations already exist in weather_stations
        logger.info("Checking existing stations in weather_stations table...")
        
        result = conn.execute(text("""
            SELECT name FROM weather_stations WHERE data_source = 'BOM';
        """))
        
        existing_stations = set(row[0] for row in result)
        logger.info(f"Found {len(existing_stations)} existing BOM stations")
        
        # Filter out existing stations
        new_stations = [s for s in unique_stations if s['name'] not in existing_stations]
        logger.info(f"Need to create {len(new_stations)} new station records")
        
        if not new_stations:
            logger.info("All stations already exist in weather_stations table")
            return
        
        # Insert new stations
        logger.info("Inserting new stations into weather_stations table...")
        
        try:
            inserted_count = 0
            for station in new_stations:
                # Generate a code from the station name (simple approach)
                code = station['name'].replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_').upper()
                code = f"BOM_{code[:20]}"  # Limit length and add BOM prefix
                
                # Insert station record
                conn.execute(text("""
                    INSERT INTO weather_stations (name, code, country, state, data_source, is_active, created_at, updated_at)
                    VALUES (:name, :code, 'Australia', 'NSW', 'BOM', true, NOW(), NOW())
                    ON CONFLICT (code) DO NOTHING;
                """), {
                    'name': station['name'],
                    'code': code
                })
                
                inserted_count += 1
                
                if inserted_count % 50 == 0:
                    logger.info(f"Inserted {inserted_count}/{len(new_stations)} stations...")
            
            conn.commit()
            logger.info(f"Successfully inserted {inserted_count} new weather stations")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting stations: {e}")
            raise
        
        # Final verification
        result = conn.execute(text("""
            SELECT COUNT(*) FROM weather_stations WHERE data_source = 'BOM';
        """))
        total_bom_stations = result.scalar()
        
        result = conn.execute(text("""
            SELECT COUNT(*) FROM weather_stations WHERE data_source = 'BOM' AND location IS NULL;
        """))
        missing_coords = result.scalar()
        
        logger.info("=" * 50)
        logger.info("STATION EXTRACTION COMPLETED")
        logger.info("=" * 50)
        logger.info(f"Total BOM stations in database: {total_bom_stations}")
        logger.info(f"Stations missing coordinates: {missing_coords}")
        logger.info(f"Ready for geocoding: {missing_coords > 0}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract and populate weather stations from BOM data")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    logger.info("Starting station extraction process...")
    extract_and_populate_stations(dry_run=args.dry_run)

if __name__ == "__main__":
    main()