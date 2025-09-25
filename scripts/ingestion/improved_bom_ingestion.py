#!/usr/bin/env python3
"""
Improved BOM Weather Data Ingestion Script

This script extracts station information directly from CSV files during ingestion,
eliminating the need for post-processing and ensuring data integrity.

Features:
- Extracts station name, state, and location from CSV headers and file paths
- Creates station records automatically during data ingestion
- Uses file path structure to determine state information
- Maintains data integrity by processing stations and weather data together
- Handles multiple encoding formats automatically
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import logging
from datetime import datetime
import pandas as pd

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.connection import SessionLocal, engine
from scripts.bom_models import BOMWeatherData, BOMWeatherStation, BOMBase
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedBOMIngestor:
    """Improved BOM data ingestor that extracts station info from CSV files"""

    def __init__(self, data_directory: str = "../data/bom_data"):
        self.data_directory = Path(data_directory)
        
        # Create separate session for BOM models
        from sqlalchemy.orm import sessionmaker
        BOMSession = sessionmaker(bind=engine)
        self.session = BOMSession()
        
        # Ensure BOM tables exist
        BOMBase.metadata.create_all(bind=engine)
        
        self.stats = {
            'files_processed': 0,
            'stations_created': 0,
            'records_inserted': 0,
            'errors': 0
        }

        # State mapping from file paths
        self.state_mapping = {
            'NSW': 'NSW',
            'VIC': 'VIC',
            'QLD': 'QLD',
            'WA': 'WA',
            'SA': 'SA',
            'TAS': 'TAS',
            'NT': 'NT',
            'ACT': 'ACT'
        }

    def extract_station_info_from_csv(self, file_path: Path) -> Optional[Dict]:
        """Extract station information directly from CSV file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']

            for encoding in encodings:
                try:
                    # Read first few lines to extract metadata
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = [f.readline().strip() for _ in range(15)]

                    # Extract station code from line 1
                    station_code = None
                    if lines[0]:
                        # Remove quotes and commas, take first part
                        station_code = lines[0].strip("'").split(',')[0]

                    # Extract station name and state from line 5
                    station_name = None
                    state = None
                    if len(lines) > 4 and 'for ' in lines[4] and ' Australia' in lines[4]:
                        # Format: "Daily ... for STATION NAME STATE Australia for ..."
                        title_line = lines[4]
                        # Extract station name and state from title
                        match = re.search(r'for (.+?) (Western|South|New South Wales|Victoria|Queensland|Tasmania|Northern Territory|Australian Capital Territory) Australia', title_line)
                        if match:
                            station_name = match.group(1).strip()
                            state_name = match.group(2).strip()

                            # Map state name to code
                            state_mapping = {
                                'Western': 'WA',
                                'South': 'SA',
                                'New South Wales': 'NSW',
                                'Victoria': 'VIC',
                                'Queensland': 'QLD',
                                'Tasmania': 'TAS',
                                'Northern Territory': 'NT',
                                'Australian Capital Territory': 'ACT'
                            }

                            state = state_mapping.get(state_name)

                    # If state not found in header, try to extract from file path
                    if not state:
                        path_parts = file_path.parts
                        for part in reversed(path_parts):
                            if part in self.state_mapping:
                                state = self.state_mapping[part]
                                break

                    # If station name not found in header, try to get from data
                    if not station_name:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding, skiprows=8)
                            if not df.empty and len(df.columns) > 0:
                                # Station name is typically in the first column, first data row
                                station_name = str(df.iloc[3, 0]).strip()
                        except:
                            pass

                    if not station_name:
                        logger.warning(f"Could not extract station name from {file_path}")
                        continue

                    # Generate station code if not found
                    if not station_code:
                        station_code = self.generate_station_code(station_name)

                    station_info = {
                        'station_name': station_name,
                        'station_code': station_code,
                        'state': state or 'UNKNOWN',
                        'country': 'Australia',
                        'data_source': 'BOM',
                        'file_path': str(file_path)
                    }

                    logger.info(f"Extracted station info: {station_name} ({state}) from {file_path.name}")
                    return station_info

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Error reading {file_path} with {encoding}: {e}")
                    continue

            logger.error(f"Could not read file {file_path} with any encoding")
            return None

        except Exception as e:
            logger.error(f"Error extracting station info from {file_path}: {e}")
            return None

    def generate_station_code(self, station_name: str) -> str:
        """Generate a unique station code from station name"""
        # Clean the station name and create a code
        code = re.sub(r'[^\w\s]', '', station_name.upper())
        code = re.sub(r'\s+', '_', code.strip())
        # Truncate if too long
        return code[:50] if len(code) > 50 else code

    def get_or_create_station(self, station_info: Dict) -> Optional[BOMWeatherStation]:
        """Get existing station or create new one"""
        try:
            # Try to find existing station
            station = self.session.query(BOMWeatherStation).filter_by(
                station_code=station_info['station_code']
            ).first()

            if not station:
                # Create new station
                station = BOMWeatherStation(
                    station_name=station_info['station_name'],
                    station_code=station_info['station_code'],
                    state=station_info['state'],
                    country=station_info['country'],
                    data_source=station_info['data_source'],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(station)
                self.session.flush()  # To get the ID
                logger.info(f"Created new station: {station_info['station_name']} ({station_info['station_code']})")
                self.stats['stations_created'] += 1
            else:
                logger.debug(f"Found existing station: {station.station_name}")

            return station

        except Exception as e:
            logger.error(f"Error creating/getting station {station_info.get('station_name', 'Unknown')}: {e}")
            self.session.rollback()
            return None

    def process_csv_file(self, file_path: Path) -> bool:
        """Process a single CSV file"""
        try:
            logger.info(f"Processing file: {file_path.name}")

            # Extract station information from CSV
            station_info = self.extract_station_info_from_csv(file_path)
            if not station_info:
                logger.error(f"Could not extract station info from {file_path}")
                return False

            # Get or create station
            station = self.get_or_create_station(station_info)
            if not station:
                logger.error(f"Could not create/get station for {file_path}")
                return False

            # Process weather data
            success = self.process_weather_data(file_path, station)
            if success:
                self.stats['files_processed'] += 1
                logger.info(f"Successfully processed {file_path.name}")
                return True
            else:
                logger.error(f"Failed to process weather data for {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors'] += 1
            return False

    def process_weather_data(self, file_path: Path, station: BOMWeatherStation) -> bool:
        """Process weather data from CSV file"""
        try:
            # Try different encodings for reading CSV data
            df = None
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, skiprows=8, encoding=encoding)
                    if not df.empty:
                        break
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
            
            if df is None or df.empty:
                logger.warning(f"No data found in {file_path} with any encoding")
                return False

            records_inserted = 0

            for idx, row in df.iterrows():
                # Skip header rows (first 3 rows are headers/units)
                if idx < 3:
                    continue
                    
                try:
                    # Parse date from 'Unnamed: 1' column
                    date_str = str(row['Unnamed: 1']).strip()
                    if not date_str or date_str == 'nan' or date_str == 'Date':
                        continue
                    try:
                        # Try different date formats
                        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']:
                            try:
                                date_obj = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        else:
                            logger.warning(f"Could not parse date: {date_str}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error parsing date {date_str}: {e}")
                        continue

                    # Check if record already exists
                    existing_record = self.session.query(BOMWeatherData).filter_by(
                        station_id=station.id,
                        observation_date=date_obj
                    ).first()

                    if existing_record:
                        logger.debug(f"Record already exists for {station.station_name} on {date_obj}")
                        continue

                    # Create new weather record
                    weather_record = BOMWeatherData(
                        station_id=station.id,
                        observation_date=date_obj,
                        evapotranspiration_mm=self.safe_float(row.get('Evapo-')),
                        rainfall_mm=self.safe_float(row.get('Unnamed: 3')),
                        pan_evaporation_mm=self.safe_float(row.get('Pan')) if row.get('Pan') and str(row.get('Pan')).strip() else None,
                        max_temperature=self.safe_float(row.get('Unnamed: 5')),
                        min_temperature=self.safe_float(row.get('Unnamed: 6')),
                        max_relative_humidity=self.safe_float(row.get('Maximum')),
                        min_relative_humidity=self.safe_float(row.get('Minimum')),
                        wind_speed_ms=self.safe_float(row.get('Average')),
                        solar_radiation_mj=self.safe_float(row.get('Unnamed: 10')),
                        file_source=file_path.name,
                        created_at=datetime.utcnow()
                    )

                    self.session.add(weather_record)
                    records_inserted += 1

                except Exception as e:
                    logger.warning(f"Error processing row: {e}")
                    continue

            self.session.commit()
            self.stats['records_inserted'] += records_inserted
            logger.info(f"Inserted {records_inserted} records for {station.station_name}")
            return True

        except Exception as e:
            logger.error(f"Error processing weather data from {file_path}: {e}")
            self.session.rollback()
            return False

    def safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if pd.isna(value) or value == '' or value == ' ':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def find_csv_files(self) -> List[Path]:
        """Find all CSV files in the data directory"""
        if not self.data_directory.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_directory}")

        csv_files = list(self.data_directory.rglob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files")
        return csv_files

    def run_ingestion(self, limit: Optional[int] = None) -> Dict:
        """Run the complete ingestion process"""
        logger.info("Starting improved BOM data ingestion...")

        # Find all CSV files
        csv_files = self.find_csv_files()

        if limit:
            csv_files = csv_files[:limit]
            logger.info(f"Limited to first {limit} files for testing")

        # Process each file
        successful_files = 0
        for file_path in csv_files:
            if self.process_csv_file(file_path):
                successful_files += 1

        # Final commit
        try:
            self.session.commit()
        except Exception as e:
            logger.error(f"Error in final commit: {e}")
            self.session.rollback()

        logger.info("Ingestion process completed!")
        logger.info(f"Files processed: {successful_files}/{len(csv_files)}")
        logger.info(f"Stations created: {self.stats['stations_created']}")
        logger.info(f"Records inserted: {self.stats['records_inserted']}")
        logger.info(f"Errors: {self.stats['errors']}")

        return self.stats

    def __del__(self):
        """Cleanup session"""
        if hasattr(self, 'session'):
            self.session.close()

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Improved BOM Weather Data Ingestion')
    parser.add_argument('--data-dir', default='../data/bom_data',
                       help='Directory containing CSV files')
    parser.add_argument('--limit', type=int,
                       help='Limit number of files to process (for testing)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    ingestor = ImprovedBOMIngestor(args.data_dir)

    try:
        stats = ingestor.run_ingestion(limit=args.limit)

        print("\n" + "="*60)
        print("IMPROVED BOM DATA INGESTION SUMMARY")
        print("="*60)
        print(f"Files processed: {stats['files_processed']}")
        print(f"Stations created: {stats['stations_created']}")
        print(f"Records inserted: {stats['records_inserted']}")
        print(f"Errors: {stats['errors']}")
        print("="*60)

        if stats['errors'] > 0:
            print("⚠️  Some errors occurred. Check improved_ingestion.log for details.")
        else:
            print("✅ Ingestion completed successfully!")

    except Exception as e:
        logger.error(f"Critical error during ingestion: {e}")
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()