#!/usr/bin/env python3
"""
Test script for database connection and small-scale ingestion
"""

import os
import sys
import logging
from weather_data.ingest_bom_data import BOMDataCleaner, BOMDataIngester
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_ingestion():
    """Test database connection and ingestion with a few files"""
    
    data_directory = "./data/bom_data"
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/weatherdb")
    
    logger.info(f"Testing database ingestion")
    logger.info(f"Data directory: {data_directory}")
    logger.info(f"Database URL: {database_url}")
    
    # Get first 3 CSV files for testing
    csv_files = glob.glob(os.path.join(data_directory, "*.csv"))[:3]
    
    if not csv_files:
        logger.error("No CSV files found for testing")
        return False
    
    logger.info(f"Testing with {len(csv_files)} files")
    
    try:
        # Step 1: Clean the data
        logger.info("Step 1: Cleaning data...")
        cleaner = BOMDataCleaner()
        cleaned_dataframes = []
        
        for file_path in csv_files:
            df = cleaner.clean_csv_file(file_path)
            if df is not None and not df.empty:
                cleaned_dataframes.append(df)
        
        if not cleaned_dataframes:
            logger.error("No cleaned data to test with")
            return False
        
        total_records = sum(len(df) for df in cleaned_dataframes)
        logger.info(f"Cleaned {len(cleaned_dataframes)} files with {total_records} total records")
        
        # Step 2: Test database connection and ingestion
        logger.info("Step 2: Testing database connection...")
        ingester = BOMDataIngester(database_url)
        
        logger.info("✅ Database connection successful!")
        logger.info("Step 3: Ingesting test data...")
        
        ingester.ingest_dataframes(cleaned_dataframes, batch_size=50)
        
        logger.info("✅ Database ingestion successful!")
        
        # Step 4: Verify data was inserted
        logger.info("Step 4: Verifying data insertion...")
        from sqlalchemy import text
        
        result = ingester.session.execute(text("SELECT COUNT(*) FROM bom_weather_data"))
        count = result.scalar()
        logger.info(f"Total records in database: {count}")
        
        # Get a sample of inserted data
        result = ingester.session.execute(text("""
            SELECT station_name, date, max_temperature_c, rain_mm 
            FROM bom_weather_data 
            ORDER BY date DESC 
            LIMIT 5
        """))
        
        logger.info("Sample inserted records:")
        for row in result:
            logger.info(f"  {row[0]} | {row[1]} | Temp: {row[2]}°C | Rain: {row[3]}mm")
        
        ingester.close()
        
        logger.info("🎉 Database ingestion test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database ingestion test failed: {str(e)}")
        logger.exception("Full error details:")
        return False

if __name__ == "__main__":
    success = test_database_ingestion()
    if success:
        logger.info("🎉 Full pipeline test passed!")
        sys.exit(0)
    else:
        logger.error("❌ Pipeline test failed!")
        sys.exit(1)
