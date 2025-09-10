#!/usr/bin/env python3
"""
Test script for BOM data cleaning - tests on a few files only
"""

import os
import sys
import logging
from weather_data.ingest_bom_data import BOMDataCleaner
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_cleaning():
    """Test the data cleaning on a few CSV files"""
    
    data_directory = "./data/bom_data"
    
    if not os.path.exists(data_directory):
        logger.error(f"Data directory not found: {data_directory}")
        return False
    
    # Get first 3 CSV files for testing
    csv_files = glob.glob(os.path.join(data_directory, "*.csv"))[:3]
    
    if not csv_files:
        logger.error("No CSV files found for testing")
        return False
    
    logger.info(f"Testing with {len(csv_files)} files: {[os.path.basename(f) for f in csv_files]}")
    
    cleaner = BOMDataCleaner()
    
    for file_path in csv_files:
        logger.info(f"\n--- Testing file: {os.path.basename(file_path)} ---")
        
        # Test individual file cleaning
        df = cleaner.clean_csv_file(file_path)
        
        if df is not None:
            logger.info(f"✅ Successfully cleaned file")
            logger.info(f"   Records: {len(df)}")
            logger.info(f"   Columns: {list(df.columns)}")
            logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
            logger.info(f"   Sample station names: {df['station_name'].unique()[:3].tolist()}")
            
            # Show a few sample records
            logger.info("   Sample records:")
            for i, row in df.head(3).iterrows():
                logger.info(f"     {row['station_name']} | {row['date'].strftime('%Y-%m-%d')} | Temp: {row['max_temperature_c']}°C | Rain: {row['rain_mm']}mm")
        else:
            logger.error(f"❌ Failed to clean file")
    
    logger.info(f"\n--- Test Summary ---")
    logger.info(f"Files processed: {cleaner.processed_files}")
    logger.info(f"Total records: {cleaner.total_records}")
    logger.info(f"Errors: {len(cleaner.errors)}")
    
    if cleaner.errors:
        logger.warning("Errors encountered:")
        for error in cleaner.errors:
            logger.warning(f"  - {error}")
    
    return len(cleaner.errors) == 0

if __name__ == "__main__":
    success = test_data_cleaning()
    if success:
        logger.info("🎉 Data cleaning test passed!")
        sys.exit(0)
    else:
        logger.error("❌ Data cleaning test failed!")
        sys.exit(1)
