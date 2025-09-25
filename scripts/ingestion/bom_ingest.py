"""
BOM Weather Data Ingestion Script
Ingests CSV weather data from Bureau of Meteorology into PostgreSQL database
"""

import os
import pandas as pd
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.database.connection import get_db, engine
from bom_models import BOMWeatherStation, BOMWeatherData, BOMDataIngestionLog, Base
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bom_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def detect_file_encoding(file_path: Path) -> str:
    """Detect the encoding of a file by trying different encodings"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # Try to read first 1KB
            return encoding
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, return utf-8 with error replacement
    return 'utf-8'

class BOMDataIngestor:
    """Handles ingestion of BOM weather data from CSV files"""
    
    def __init__(self, data_directory: str = "./data/bom_data"):
        self.data_directory = Path(data_directory)
        self.session = None
        self.stats = {
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'total_records': 0,
            'successful_records': 0,
            'skipped_records': 0
        }
        
    def setup_database(self):
        """Create tables if they don't exist"""
        try:
            logger.info("Setting up database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        if not self.session:
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.session = SessionLocal()
        return self.session
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()
            self.session = None
    
    def extract_station_info(self, filename: str) -> Dict[str, str]:
        """Extract station information from filename"""
        # Remove .csv extension and split by '-'
        base_name = filename.replace('.csv', '')
        parts = base_name.split('-')
        
        if len(parts) != 2:
            logger.warning(f"Unexpected filename format: {filename}")
            return {'name': base_name, 'code': base_name}
        
        station_name = parts[0].replace('_', ' ').title()
        year_month = parts[1]
        
        # Generate a station code
        station_code = parts[0].upper()
        
        return {
            'name': station_name,
            'code': station_code,
            'year_month': year_month
        }
    
    def parse_csv_file(self, file_path: Path) -> Tuple[Dict, pd.DataFrame]:
        """Parse BOM CSV file and extract header info and data"""
        try:
            # Read the first few lines to understand structure with proper encoding detection
            encoding = detect_file_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                lines = [f.readline().strip() for _ in range(15)]
            
            # Find where the actual data starts (after headers)
            data_start_line = 0
            for i, line in enumerate(lines):
                if line.startswith('Station Name,') or 'Date' in line:
                    data_start_line = i
                    break
            
            if data_start_line == 0:
                # Fallback: assume data starts at line 8 (typical BOM format)
                data_start_line = 8
            
            # Read the CSV data with proper encoding detection
            encoding = detect_file_encoding(file_path)
            df = pd.read_csv(file_path, skiprows=data_start_line, encoding=encoding)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Extract header information
            header_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'data_start_line': data_start_line
            }
            
            logger.debug(f"Parsed {file_path.name}: {len(df)} rows, columns: {list(df.columns)}")
            return header_info, df
            
        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path}: {e}")
            raise
    
    def clean_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate weather data"""
        original_count = len(df)
        
        # Standardize column names mapping
        column_mapping = {
            'Station Name': 'station_name',
            'Date': 'date',
            'Evapotranspiration (mm)': 'evapotranspiration_mm',
            'Evapotranspiration (mm) 0000-2400': 'evapotranspiration_mm',
            'Rain (mm)': 'rainfall_mm',
            'Rain (mm) 0900-0900': 'rainfall_mm',
            'Pan evaporation (mm)': 'pan_evaporation_mm',
            'Pan evaporation (mm) 0900-0900': 'pan_evaporation_mm',
            'Maximum temperature (°C)': 'max_temperature',
            'Minimum temperature (°C)': 'min_temperature',
            'Maximum relative humidity (%)': 'max_relative_humidity',
            'Minimum relative humidity (%)': 'min_relative_humidity',
            'Average 10m wind speed (m/sec)': 'wind_speed_ms',
            'Solar radiation (MJ/sq m)': 'solar_radiation_mj'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Remove rows with invalid dates
            df = df.dropna(subset=['date'])
        
        # Clean numeric columns
        numeric_columns = [
            'evapotranspiration_mm', 'rainfall_mm', 'pan_evaporation_mm',
            'max_temperature', 'min_temperature', 'max_relative_humidity',
            'min_relative_humidity', 'wind_speed_ms', 'solar_radiation_mj'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                # Replace common non-numeric values
                df[col] = df[col].replace(['', '-', 'N/A', 'NA', '##'], None)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove completely empty rows
        df = df.dropna(how='all', subset=numeric_columns)
        
        cleaned_count = len(df)
        logger.debug(f"Data cleaning: {original_count} -> {cleaned_count} rows")
        
        return df
    
    def get_or_create_station(self, station_info: Dict[str, str]) -> BOMWeatherStation:
        """Get existing station or create new one"""
        session = self.get_session()
        
        # Try to find existing station
        station = session.query(BOMWeatherStation).filter_by(
            station_code=station_info['code']
        ).first()
        
        if not station:
            # Create new station
            station = BOMWeatherStation(
                station_name=station_info['name'],
                station_code=station_info['code'],
                state='NSW',  # All our data is NSW
                country='Australia',
                data_source='BOM',
                is_active=True
            )
            session.add(station)
            session.flush()  # To get the ID
            logger.info(f"Created new station: {station_info['name']} ({station_info['code']})")
        
        return station
    
    def ingest_file_data(self, file_path: Path) -> BOMDataIngestionLog:
        """Ingest data from a single CSV file"""
        log_entry = BOMDataIngestionLog(
            filename=file_path.name,
            file_path=str(file_path),
            ingestion_start=datetime.now(),
            status='processing'
        )
        
        session = self.get_session()
        session.add(log_entry)
        session.flush()
        
        try:
            # Extract station information
            station_info = self.extract_station_info(file_path.name)
            log_entry.station_name = station_info['name']
            
            # Parse CSV file
            header_info, df = self.parse_csv_file(file_path)
            
            # Clean data
            df = self.clean_weather_data(df)
            log_entry.records_processed = len(df)
            
            if len(df) == 0:
                log_entry.status = 'failed'
                log_entry.error_message = 'No valid data rows found'
                session.commit()
                return log_entry
            
            # Get or create station
            station = self.get_or_create_station(station_info)
            
            # Process weather data
            records_inserted = 0
            records_updated = 0
            records_skipped = 0
            
            for _, row in df.iterrows():
                try:
                    # Check if record already exists
                    existing_record = session.query(BOMWeatherData).filter_by(
                        station_id=station.id,
                        observation_date=row['date'].date()
                    ).first()
                    
                    if existing_record:
                        # Update existing record
                        for col in ['evapotranspiration_mm', 'rainfall_mm', 'pan_evaporation_mm',
                                  'max_temperature', 'min_temperature', 'max_relative_humidity',
                                  'min_relative_humidity', 'wind_speed_ms', 'solar_radiation_mj']:
                            if col in row and pd.notna(row[col]):
                                setattr(existing_record, col, row[col])
                        
                        existing_record.file_source = file_path.name
                        records_updated += 1
                    else:
                        # Create new record
                        weather_record = BOMWeatherData(
                            station_id=station.id,
                            observation_date=row['date'].date(),
                            evapotranspiration_mm=row.get('evapotranspiration_mm'),
                            rainfall_mm=row.get('rainfall_mm'),
                            pan_evaporation_mm=row.get('pan_evaporation_mm'),
                            max_temperature=row.get('max_temperature'),
                            min_temperature=row.get('min_temperature'),
                            max_relative_humidity=row.get('max_relative_humidity'),
                            min_relative_humidity=row.get('min_relative_humidity'),
                            wind_speed_ms=row.get('wind_speed_ms'),
                            solar_radiation_mj=row.get('solar_radiation_mj'),
                            file_source=file_path.name,
                            data_source='BOM'
                        )
                        session.add(weather_record)
                        records_inserted += 1
                
                except Exception as e:
                    logger.warning(f"Error processing row in {file_path.name}: {e}")
                    records_skipped += 1
                    continue
            
            # Update log entry
            log_entry.records_inserted = records_inserted
            log_entry.records_updated = records_updated
            log_entry.records_skipped = records_skipped
            log_entry.ingestion_end = datetime.now()
            log_entry.status = 'success'
            
            # Commit all changes
            session.commit()
            
            logger.info(f"Successfully ingested {file_path.name}: "
                       f"{records_inserted} inserted, {records_updated} updated, "
                       f"{records_skipped} skipped")
            
            return log_entry
            
        except Exception as e:
            session.rollback()
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.ingestion_end = datetime.now()
            session.commit()
            
            logger.error(f"Failed to ingest {file_path.name}: {e}")
            logger.error(traceback.format_exc())
            return log_entry
    
    def ingest_all_files(self, limit: Optional[int] = None) -> Dict:
        """Ingest all CSV files in the data directory"""
        if not self.data_directory.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_directory}")
        
        # Find all CSV files
        csv_files = list(self.data_directory.glob("*.csv"))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {self.data_directory}")
            return self.stats
        
        if limit:
            csv_files = csv_files[:limit]
            logger.info(f"Processing first {limit} files (limit applied)")
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        # Setup database
        self.setup_database()
        
        # Process each file
        for i, file_path in enumerate(csv_files, 1):
            logger.info(f"Processing file {i}/{len(csv_files)}: {file_path.name}")
            
            try:
                log_entry = self.ingest_file_data(file_path)
                
                self.stats['files_processed'] += 1
                if log_entry.status == 'success':
                    self.stats['files_successful'] += 1
                    self.stats['successful_records'] += log_entry.records_inserted + log_entry.records_updated
                    self.stats['skipped_records'] += log_entry.records_skipped
                else:
                    self.stats['files_failed'] += 1
                
                self.stats['total_records'] += log_entry.records_processed
                
            except Exception as e:
                self.stats['files_failed'] += 1
                logger.error(f"Critical error processing {file_path.name}: {e}")
                continue
        
        # Close database connection
        self.close_session()
        
        return self.stats
    
    def print_summary(self):
        """Print ingestion summary"""
        print("\n" + "="*60)
        print("BOM DATA INGESTION SUMMARY")
        print("="*60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files successful: {self.stats['files_successful']}")
        print(f"Files failed: {self.stats['files_failed']}")
        print(f"Total records processed: {self.stats['total_records']}")
        print(f"Successful records: {self.stats['successful_records']}")
        print(f"Skipped records: {self.stats['skipped_records']}")
        print("="*60)

def main():
    """Main ingestion function"""
    print("Starting BOM Weather Data Ingestion...")
    
    # Create ingestor
    ingestor = BOMDataIngestor()
    
    try:
        # Run ingestion with a test limit first
        print("Running test ingestion (first 5 files)...")
        stats = ingestor.ingest_all_files(limit=5)
        ingestor.print_summary()
        
        # Ask user if they want to continue with all files
        response = input("\nTest successful! Process all files? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("Processing all files...")
            ingestor = BOMDataIngestor()  # Reset stats
            stats = ingestor.ingest_all_files()
            ingestor.print_summary()
        
    except Exception as e:
        logger.error(f"Critical error during ingestion: {e}")
        logger.error(traceback.format_exc())
    
    print("Ingestion process completed.")

if __name__ == "__main__":
    main()
