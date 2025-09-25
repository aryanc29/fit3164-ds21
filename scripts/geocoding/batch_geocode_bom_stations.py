#!/usr/bin/env python3
"""
Batch geocoding script for BOM Weather Stations
Populates latitude/longitude columns in bom_weather_stations table
"""
import os
import sys
import time
import requests
import logging
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

class BOMStationGeocoder:
    def __init__(self, database_url, delay=1.2):
        """
        Initialize the BOM station geocoder
        
        Args:
            database_url: PostgreSQL connection string
            delay: Delay between API requests (seconds) - Nominatim requires 1+ second
        """
        self.database_url = database_url
        self.delay = delay
        self.session = None
        self.setup_logging()
        self.setup_database()
        
        # Nominatim API configuration
        self.nominatim_base = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'NSW-Weather-Dashboard/1.0 (weather-dashboard@example.com)'
        }
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('bom_geocoding.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """Setup database connection"""
        try:
            engine = create_engine(self.database_url)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            self.logger.info(f"Connected to database: {self.database_url.split('@')[1] if '@' in self.database_url else 'localhost'}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_stations_missing_coordinates(self, limit=None):
        """Get stations from bom_weather_stations that don't have coordinates"""
        try:
            query = text("""
                SELECT id, station_name, station_code, state
                FROM bom_weather_stations 
                WHERE latitude IS NULL OR longitude IS NULL
                ORDER BY id
            """)
            
            if limit:
                query = text(str(query) + f" LIMIT {limit}")
            
            result = self.session.execute(query)
            stations = result.fetchall()
            
            self.logger.info(f"Found {len(stations)} stations missing coordinates")
            return stations
            
        except Exception as e:
            self.logger.error(f"Error querying stations: {e}")
            return []
    
    def geocode_station(self, station_name, state=None):
        """
        Geocode a station using multiple search strategies
        
        Args:
            station_name: Name of the weather station
            state: State code (NSW, VIC, etc.)
            
        Returns:
            tuple: (latitude, longitude) or (None, None) if not found
        """
        search_queries = [
            f"{station_name}, Australia",
            f"{station_name} weather station, Australia",
            f"{station_name} airport, Australia",
            f"{station_name}, {state}, Australia" if state else None,
            f"{station_name.replace('AIRPORT', '').strip()}, Australia",
            f"{station_name.replace('(', '').replace(')', '')}, Australia"
        ]
        
        # Remove None values
        search_queries = [q for q in search_queries if q]
        
        for query in search_queries:
            try:
                params = {
                    'q': query,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'au',  # Restrict to Australia
                    'addressdetails': 1
                }
                
                response = requests.get(
                    self.nominatim_base,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        result = results[0]
                        lat = float(result['lat'])
                        lon = float(result['lon'])
                        
                        # Basic validation - ensure coordinates are in Australia
                        if -45 <= lat <= -10 and 110 <= lon <= 155:
                            self.logger.debug(f"Found coordinates for '{station_name}' using query '{query}': {lat}, {lon}")
                            return lat, lon
                
                # Rate limiting between API requests
                time.sleep(self.delay)
                
            except Exception as e:
                self.logger.warning(f"Error geocoding with query '{query}': {e}")
                continue
        
        return None, None
    
    def update_station_coordinates(self, station_id, latitude, longitude):
        """Update station coordinates in the database"""
        try:
            update_query = text("""
                UPDATE bom_weather_stations 
                SET latitude = :lat, longitude = :lon, updated_at = :updated
                WHERE id = :id
            """)
            
            self.session.execute(update_query, {
                'id': station_id,
                'lat': latitude,
                'lon': longitude,
                'updated': datetime.now()
            })
            
            self.session.commit()
            self.logger.info(f"Updated station {station_id} with coordinates: {latitude}, {longitude}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating station {station_id}: {e}")
            self.session.rollback()
            return False
    
    def process_batch(self, stations, dry_run=False, batch_delay=30):
        """Process a batch of stations with enhanced timing controls"""
        successful = 0
        failed = 0
        skipped = 0
        
        self.logger.info(f"Processing batch of {len(stations)} stations...")
        
        for i, station in enumerate(stations, 1):
            self.logger.info(f"[{i}] Processing station: {station.station_name} (ID: {station.id})")
            
            if dry_run:
                self.logger.info(f"DRY RUN: Would geocode '{station.station_name}'")
                successful += 1
                # Add delay even in dry run for realistic timing
                time.sleep(0.1)
                continue
            
            # Geocode the station
            lat, lon = self.geocode_station(station.station_name, station.state)
            
            if lat and lon:
                if self.update_station_coordinates(station.id, lat, lon):
                    successful += 1
                else:
                    failed += 1
            else:
                self.logger.warning(f"Failed to geocode station '{station.station_name}' with any search strategy")
                self.logger.warning(f"Skipping station {station.station_name} - no coordinates found")
                skipped += 1
            
            # Add delay between stations (2 seconds as requested)
            if i < len(stations):  # Don't delay after the last station in batch
                self.logger.debug(f"Waiting {self.delay} seconds before next station...")
                time.sleep(self.delay)
        
        # Add batch delay after completing the batch (except for last batch)
        if not dry_run and batch_delay > 0:
            self.logger.info(f"Batch completed. Waiting {batch_delay} seconds before next batch...")
            time.sleep(batch_delay)
        
        return successful, failed, skipped
    
    def run_batch_geocoding(self, batch_size=50, max_stations=None, dry_run=False, batch_delay=30):
        """Run the complete batch geocoding process with enhanced timing controls"""
        self.logger.info("Starting batch geocoding process...")
        self.logger.info(f"Batch size: {batch_size}")
        self.logger.info(f"Station delay: {self.delay} seconds")
        self.logger.info(f"Batch delay: {batch_delay} seconds")
        self.logger.info(f"Dry run: {dry_run}")
        self.logger.info(f"Database URL: {self.database_url.split('@')[1] if '@' in self.database_url else 'localhost'}")
        
        # Get stations missing coordinates
        stations = self.get_stations_missing_coordinates(limit=max_stations)
        
        if not stations:
            self.logger.info("No stations missing coordinates found!")
            return
        
        total_stations = len(stations)
        total_successful = 0
        total_failed = 0
        total_skipped = 0
        
        # Calculate estimated time
        if not dry_run:
            estimated_time = (total_stations * self.delay) + ((total_stations // batch_size) * batch_delay)
            self.logger.info(f"Estimated processing time: {estimated_time/60:.1f} minutes for {total_stations} stations")
        
        start_time = time.time()
        
        # Process in batches
        for batch_num in range(0, total_stations, batch_size):
            batch_end = min(batch_num + batch_size, total_stations)
            batch = stations[batch_num:batch_end]
            
            batch_number = (batch_num // batch_size) + 1
            total_batches = (total_stations + batch_size - 1) // batch_size
            
            self.logger.info(f"Processing batch {batch_number}/{total_batches} ({len(batch)} stations)")
            
            # Don't add batch delay for the last batch
            current_batch_delay = batch_delay if batch_number < total_batches else 0
            
            successful, failed, skipped = self.process_batch(batch, dry_run, current_batch_delay)
            
            total_successful += successful
            total_failed += failed
            total_skipped += skipped
            
            # Progress update
            progress = (batch_num + len(batch)) / total_stations * 100
            elapsed_time = time.time() - start_time
            
            self.logger.info(f"Batch {batch_number} completed: {successful} successful, {failed} failed, {skipped} skipped")
            self.logger.info(f"Progress: {progress:.1f}% ({batch_num + len(batch)}/{total_stations}) - Elapsed: {elapsed_time/60:.1f} min")
        
        # Final summary
        total_time = time.time() - start_time
        self.logger.info("=" * 60)
        self.logger.info("BATCH GEOCODING COMPLETED")
        self.logger.info("=" * 60)
        self.logger.info(f"Total processed: {total_stations}")
        self.logger.info(f"Successful: {total_successful} ({total_successful/total_stations*100:.1f}%)")
        self.logger.info(f"Failed: {total_failed}")
        self.logger.info(f"Skipped: {total_skipped}")
        self.logger.info(f"Total time: {total_time/60:.1f} minutes")
        
        if not dry_run and total_successful > 0:
            self.logger.info(f"Success! {total_successful} stations now have coordinates!")

def main():
    parser = argparse.ArgumentParser(description='Batch geocode BOM weather stations')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of stations to process per batch (default: 50)')
    parser.add_argument('--max-stations', type=int, help='Maximum number of stations to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Run without making database changes')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between API requests in seconds (default: 2.0)')
    parser.add_argument('--batch-delay', type=int, default=30, help='Delay between batches in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Database configuration
    database_url = "postgresql+pg8000://postgres:password@localhost:5433/weatherdb"
    
    try:
        geocoder = BOMStationGeocoder(database_url, delay=args.delay)
        geocoder.run_batch_geocoding(
            batch_size=args.batch_size,
            max_stations=args.max_stations,
            dry_run=args.dry_run,
            batch_delay=args.batch_delay
        )
    except Exception as e:
        logging.error(f"Geocoding process failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())