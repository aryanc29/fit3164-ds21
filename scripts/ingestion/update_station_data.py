#!/usr/bin/env python3
"""
Station Data Update Script for BOM Weather Database

This script updates the bom_weather_stations table to ensure all stations
referenced in the weather data have corresponding station records.

Features:
- Identifies stations in weather data that don't exist in stations table
- Creates missing station records with basic information
- Updates existing stations with missing data
- Extracts state information from station names and file paths
- Maintains data integrity between weather data and station records
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Optional
import re
import logging
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.connection import SessionLocal, engine
from app.database.models import BOMWeatherStation, BOMWeatherData
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('station_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StationDataUpdater:
    """Updates station data to match weather records"""

    def __init__(self):
        self.session = SessionLocal()
        self.stats = {
            'stations_found': 0,
            'stations_created': 0,
            'stations_updated': 0,
            'errors': 0
        }

    def get_stations_from_weather_data(self) -> Set[str]:
        """Get all unique station names from weather data"""
        try:
            result = self.session.execute(
                text("SELECT DISTINCT station_name FROM bom_weather_data")
            )
            return {row[0] for row in result}
        except Exception as e:
            logger.error(f"Error getting stations from weather data: {e}")
            return set()

    def get_existing_stations(self) -> Set[str]:
        """Get all existing station names"""
        try:
            result = self.session.execute(
                text("SELECT station_name FROM bom_weather_stations")
            )
            return {row[0] for row in result}
        except Exception as e:
            logger.error(f"Error getting existing stations: {e}")
            return set()

    def extract_state_from_station_name(self, station_name: str) -> Optional[str]:
        """Extract state information from station name or file path"""
        # Common state indicators in station names
        state_indicators = {
            'NSW': ['NSW', 'SYDNEY', 'NEW SOUTH WALES'],
            'VIC': ['VIC', 'MELBOURNE', 'VICTORIA'],
            'QLD': ['QLD', 'BRISBANE', 'QUEENSLAND'],
            'WA': ['WA', 'PERTH', 'WESTERN AUSTRALIA'],
            'SA': ['SA', 'ADELAIDE', 'SOUTH AUSTRALIA'],
            'TAS': ['TAS', 'HOBART', 'TASMANIA'],
            'NT': ['NT', 'DARWIN', 'NORTHERN TERRITORY'],
            'ACT': ['ACT', 'CANBERRA', 'AUSTRALIAN CAPITAL TERRITORY']
        }

        station_upper = station_name.upper()

        for state, indicators in state_indicators.items():
            for indicator in indicators:
                if indicator in station_upper:
                    return state

        return None

    def generate_station_code(self, station_name: str) -> str:
        """Generate a unique station code from station name"""
        # Clean the station name and create a code
        code = re.sub(r'[^\w\s]', '', station_name.upper())
        code = re.sub(r'\s+', '_', code.strip())
        # Truncate if too long
        return code[:50] if len(code) > 50 else code

    def create_station_record(self, station_name: str) -> bool:
        """Create a new station record"""
        try:
            # Extract state from station name
            state = self.extract_state_from_station_name(station_name)

            # Generate station code
            station_code = self.generate_station_code(station_name)

            # Check if station code already exists
            existing = self.session.query(BOMWeatherStation).filter_by(
                station_code=station_code
            ).first()

            if existing:
                # Make code unique by adding suffix
                counter = 1
                while self.session.query(BOMWeatherStation).filter_by(
                    station_code=f"{station_code}_{counter}"
                ).first():
                    counter += 1
                station_code = f"{station_code}_{counter}"

            # Create new station
            station = BOMWeatherStation(
                station_name=station_name,
                station_code=station_code,
                state=state or 'UNKNOWN',
                country='Australia',
                data_source='BOM',
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(station)
            self.session.commit()

            logger.info(f"Created station: {station_name} ({station_code})")
            self.stats['stations_created'] += 1
            return True

        except Exception as e:
            logger.error(f"Error creating station {station_name}: {e}")
            self.session.rollback()
            self.stats['errors'] += 1
            return False

    def update_existing_stations(self) -> None:
        """Update existing stations with missing information"""
        try:
            stations = self.session.query(BOMWeatherStation).all()

            for station in stations:
                updated = False

                # Update state if missing
                if not station.state or station.state == 'UNKNOWN':
                    extracted_state = self.extract_state_from_station_name(station.station_name)
                    if extracted_state:
                        station.state = extracted_state
                        updated = True

                # Update timestamp
                if updated:
                    station.updated_at = datetime.utcnow()
                    self.stats['stations_updated'] += 1

            if self.stats['stations_updated'] > 0:
                self.session.commit()
                logger.info(f"Updated {self.stats['stations_updated']} existing stations")

        except Exception as e:
            logger.error(f"Error updating existing stations: {e}")
            self.session.rollback()

    def run_update(self) -> Dict:
        """Main update process"""
        logger.info("Starting station data update process...")

        # Get all stations from weather data
        weather_stations = self.get_stations_from_weather_data()
        self.stats['stations_found'] = len(weather_stations)
        logger.info(f"Found {len(weather_stations)} unique stations in weather data")

        # Get existing stations
        existing_stations = self.get_existing_stations()
        logger.info(f"Found {len(existing_stations)} existing stations")

        # Find missing stations
        missing_stations = weather_stations - existing_stations
        logger.info(f"Found {len(missing_stations)} missing stations")

        # Create missing stations
        for station_name in missing_stations:
            self.create_station_record(station_name)

        # Update existing stations
        self.update_existing_stations()

        # Final verification
        final_existing = self.get_existing_stations()
        final_missing = weather_stations - final_existing

        logger.info("Station update process completed!")
        logger.info(f"Total stations in weather data: {len(weather_stations)}")
        logger.info(f"Stations created: {self.stats['stations_created']}")
        logger.info(f"Stations updated: {self.stats['stations_updated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Remaining missing stations: {len(final_missing)}")

        if final_missing:
            logger.warning("Stations still missing:")
            for station in list(final_missing)[:10]:  # Show first 10
                logger.warning(f"  - {station}")
            if len(final_missing) > 10:
                logger.warning(f"  ... and {len(final_missing) - 10} more")

        return self.stats

    def __del__(self):
        """Cleanup session"""
        if hasattr(self, 'session'):
            self.session.close()

def main():
    """Main function"""
    updater = StationDataUpdater()
    try:
        stats = updater.run_update()

        print("\n" + "="*50)
        print("STATION DATA UPDATE SUMMARY")
        print("="*50)
        print(f"Stations found in weather data: {stats['stations_found']}")
        print(f"Stations created: {stats['stations_created']}")
        print(f"Stations updated: {stats['stations_updated']}")
        print(f"Errors: {stats['errors']}")
        print("="*50)

        if stats['errors'] > 0:
            print("⚠️  Some errors occurred. Check station_update.log for details.")
        else:
            print("✅ Station data update completed successfully!")

    except Exception as e:
        logger.error(f"Critical error during station update: {e}")
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()