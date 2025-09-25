#!/usr/bin/env python3
"""
BOM Weather Data Cleaning and Ingestion Script
Cleans BOM CSV files and loads them into PostgreSQL database
"""

import os
import pandas as pd
import re
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from typing import List, Dict, Optional
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_file_encoding(file_path) -> str:
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

Base = declarative_base()

class BOMWeatherData(Base):
    """Database model for BOM weather data"""
    __tablename__ = 'bom_weather_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String(200), nullable=False)
    date = Column(Date, nullable=False)
    evapotranspiration_mm = Column(Float, nullable=True)  # 0000-2400
    rain_mm = Column(Float, nullable=True)  # 0900-0900
    pan_evaporation_mm = Column(Float, nullable=True)  # 0900-0900
    max_temperature_c = Column(Float, nullable=True)
    min_temperature_c = Column(Float, nullable=True)
    max_relative_humidity_pct = Column(Float, nullable=True)
    min_relative_humidity_pct = Column(Float, nullable=True)
    wind_speed_m_per_sec = Column(Float, nullable=True)  # 10m Wind Speed
    solar_radiation_mj_per_sq_m = Column(Float, nullable=True)
    file_source = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BOMWeatherData(station='{self.station_name}', date='{self.date}')>"

class BOMDataCleaner:
    """Handles cleaning and processing of BOM CSV files"""
    
    def __init__(self):
        self.processed_files = 0
        self.total_records = 0
        self.errors = []
    
    def clean_csv_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Clean a single BOM CSV file by removing headers and extracting data
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Cleaned DataFrame or None if processing failed
        """
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Read the entire file as text first with proper encoding detection
            encoding = detect_file_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                lines = f.readlines()
            
            # Find the actual data start (look for the line with "Station Name,Date,...")
            data_start_line = None
            for i, line in enumerate(lines):
                if 'Station Name,Date,' in line:
                    data_start_line = i + 2  # Skip the header and units line
                    break
            
            if data_start_line is None:
                logger.error(f"Could not find data start in {file_path}")
                return None
            
            # Extract data lines (skip totals and empty lines)
            data_lines = []
            for line in lines[data_start_line:]:
                line = line.strip()
                if line and not line.startswith('Totals:') and not line.startswith(','):
                    data_lines.append(line)
            
            if not data_lines:
                logger.warning(f"No data found in {file_path}")
                return None
            
            # Create a temporary CSV string with clean headers
            clean_headers = [
                'station_name', 'date', 'evapotranspiration_mm', 'rain_mm', 
                'pan_evaporation_mm', 'max_temperature_c', 'min_temperature_c',
                'max_relative_humidity_pct', 'min_relative_humidity_pct', 
                'wind_speed_m_per_sec', 'solar_radiation_mj_per_sq_m'
            ]
            
            csv_content = ','.join(clean_headers) + '\n' + '\n'.join(data_lines)
            
            # Read into pandas DataFrame
            from io import StringIO
            df = pd.read_csv(StringIO(csv_content))
            
            # Clean and process the data
            df = self._process_dataframe(df, file_path)
            
            logger.info(f"Successfully processed {len(df)} records from {file_path}")
            return df
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return None
    
    def _process_dataframe(self, df: pd.DataFrame, file_path: str) -> pd.DataFrame:
        """Process and clean the DataFrame"""
        
        # Add file source
        df['file_source'] = os.path.basename(file_path)
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
        
        # Clean numeric columns - replace empty strings and spaces with NaN
        numeric_columns = [
            'evapotranspiration_mm', 'rain_mm', 'pan_evaporation_mm',
            'max_temperature_c', 'min_temperature_c', 'max_relative_humidity_pct',
            'min_relative_humidity_pct', 'wind_speed_m_per_sec', 'solar_radiation_mj_per_sq_m'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                # Replace empty strings, spaces, and other non-numeric values with NaN
                df[col] = df[col].astype(str).replace(r'^\s*$', '', regex=True)
                df[col] = df[col].replace('', None)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['date'])
        
        # Clean station names
        df['station_name'] = df['station_name'].str.strip()
        
        return df
    
    def process_directory(self, data_directory: str) -> List[pd.DataFrame]:
        """
        Process all CSV files in a directory
        
        Args:
            data_directory: Path to directory containing CSV files
            
        Returns:
            List of cleaned DataFrames
        """
        csv_files = glob.glob(os.path.join(data_directory, "*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        cleaned_dataframes = []
        
        for file_path in csv_files:
            df = self.clean_csv_file(file_path)
            if df is not None and not df.empty:
                cleaned_dataframes.append(df)
                self.processed_files += 1
                self.total_records += len(df)
            
            # Log progress every 10 files
            if self.processed_files % 10 == 0:
                logger.info(f"Processed {self.processed_files} files, {self.total_records} total records")
        
        logger.info(f"Processing complete: {self.processed_files} files, {self.total_records} total records")
        if self.errors:
            logger.warning(f"Encountered {len(self.errors)} errors during processing")
        
        return cleaned_dataframes

class BOMDataIngester:
    """Handles database ingestion of cleaned BOM data"""
    
    def __init__(self, database_url: str):
        # Ensure we're using pg8000 driver for GPL compliance
        if "postgresql://" in database_url and "pg8000" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+pg8000://")
        
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def ingest_dataframes(self, dataframes: List[pd.DataFrame], batch_size: int = 1000):
        """
        Ingest cleaned DataFrames into the database
        
        Args:
            dataframes: List of cleaned DataFrames
            batch_size: Number of records to insert in each batch
        """
        logger.info("Starting database ingestion...")
        
        total_inserted = 0
        
        for i, df in enumerate(dataframes):
            logger.info(f"Ingesting DataFrame {i+1}/{len(dataframes)} ({len(df)} records)")
            
            try:
                # Convert DataFrame to database records
                records = []
                for _, row in df.iterrows():
                    record = BOMWeatherData(
                        station_name=row['station_name'],
                        date=row['date'].date() if pd.notna(row['date']) else None,
                        evapotranspiration_mm=row.get('evapotranspiration_mm'),
                        rain_mm=row.get('rain_mm'),
                        pan_evaporation_mm=row.get('pan_evaporation_mm'),
                        max_temperature_c=row.get('max_temperature_c'),
                        min_temperature_c=row.get('min_temperature_c'),
                        max_relative_humidity_pct=row.get('max_relative_humidity_pct'),
                        min_relative_humidity_pct=row.get('min_relative_humidity_pct'),
                        wind_speed_m_per_sec=row.get('wind_speed_m_per_sec'),
                        solar_radiation_mj_per_sq_m=row.get('solar_radiation_mj_per_sq_m'),
                        file_source=row.get('file_source')
                    )
                    records.append(record)
                    
                    # Insert in batches
                    if len(records) >= batch_size:
                        self.session.add_all(records)
                        self.session.commit()
                        total_inserted += len(records)
                        records = []
                        logger.info(f"Inserted batch, total so far: {total_inserted}")
                
                # Insert remaining records
                if records:
                    self.session.add_all(records)
                    self.session.commit()
                    total_inserted += len(records)
                
            except Exception as e:
                logger.error(f"Error ingesting DataFrame {i+1}: {str(e)}")
                self.session.rollback()
        
        logger.info(f"Database ingestion complete. Total records inserted: {total_inserted}")
    
    def close(self):
        """Close database session"""
        self.session.close()

def main():
    """Main function to run the data cleaning and ingestion pipeline"""
    folders = ['NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA']  # Exclude NSW as per instructions
    for folder in folders:
        data_dir = os.path.join("./data/bom_data", folder)
    
        # Configuration
        # DATA_DIRECTORY = "./data/bom_data/"
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/weatherdb")
        
        logger.info("Starting BOM Weather Data Cleaning and Ingestion Pipeline")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Database URL: {DATABASE_URL}")
        
        # Step 1: Clean the CSV files
        cleaner = BOMDataCleaner()
        cleaned_dataframes = cleaner.process_directory(data_dir)
        
        if not cleaned_dataframes:
            logger.error("No data to ingest. Exiting.")
            return
        
        # Step 2: Ingest into database
        ingester = BOMDataIngester(DATABASE_URL)
        try:
            ingester.ingest_dataframes(cleaned_dataframes)
        finally:
            ingester.close()
        
        logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
