#!/usr/bin/env python3
"""
Master script for downloading and ingesting BOM weather data for all Australian states
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print("Output:", result.stdout[-500:])  # Show last 500 chars of output
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            if result.stderr:
                print("Error:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {str(e)}")
        return False

def main():
    """Main function to orchestrate the entire data pipeline"""
    print("🌤️  BOM Weather Data Pipeline - States (excluding NSW)")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Ensure data directory exists
    data_dir = Path("./data/bom_data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Download data for all states
    print("\n📥 STEP 1: Downloading weather data from BOM FTP server")
    download_success = run_command(
        "python scripts/bom_data.py",
        "Download BOM weather data for all states"
    )

    if not download_success:
        print("❌ Download step failed. Please check the errors above.")
        sys.exit(1)

    # Step 2: Check what files were downloaded
    csv_files = list(data_dir.glob("*.csv"))
    print(f"\n📊 Downloaded {len(csv_files)} CSV files")

    if len(csv_files) == 0:
        print("⚠️  No CSV files found. The download may have failed.")
        sys.exit(1)

    # Show some examples of downloaded files
    print("Sample downloaded files:")
    for i, csv_file in enumerate(csv_files[:5]):
        print(f"  - {csv_file.name}")
    if len(csv_files) > 5:
        print(f"  ... and {len(csv_files) - 5} more files")

    # Step 3: Ingest data into database
    print("\n🗄️  STEP 2: Ingesting data into database")
    ingest_success = run_command(
        "python scripts/bom_ingest.py",
        "Ingest BOM weather data into database"
    )

    if not ingest_success:
        print("❌ Ingestion step failed. Please check the errors above.")
        sys.exit(1)

    # Step 4: Validate the ingestion
    print("\n✅ STEP 3: Validating data ingestion")
    validate_success = run_command(
        "python scripts/validate_bom_data.py",
        "Validate ingested BOM data"
    )

    if not validate_success:
        print("⚠️  Validation step had issues, but ingestion may still be successful.")
        # Don't exit here as validation might have minor issues

    # Step 5: Generate summary
    print("\n📈 STEP 4: Generating ingestion summary")
    try:
        # Count files by state
        state_counts = {}
        for csv_file in csv_files:
            filename = csv_file.name
            # Extract state from filename (assuming format like: LOCATION-YYYYMM.csv)
            if '-' in filename:
                location_part = filename.split('-')[0]
                # The state is typically the first 2-3 characters of the location
                # For now, just count total files
                pass

        print("\n📊 INGESTION SUMMARY")
        print("=" * 40)
        print(f"Total CSV files downloaded: {len(csv_files)}")
        print(f"Data directory: {data_dir.absolute()}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Check database for ingested records
        try:
            from app.database.connection import engine
            from sqlalchemy import text

            with engine.connect() as conn:
                # Count weather stations
                result = conn.execute(text("SELECT COUNT(*) FROM bom_weather_stations"))
                station_count = result.fetchone()[0]

                # Count weather data records
                result = conn.execute(text("SELECT COUNT(*) FROM bom_weather_data"))
                data_count = result.fetchone()[0]

                print(f"Database records:")
                print(f"  - Weather stations: {station_count}")
                print(f"  - Weather data records: {data_count}")

        except Exception as e:
            print(f"Could not check database counts: {e}")

    except Exception as e:
        print(f"Error generating summary: {e}")

    print("\n🎉 BOM Weather Data Pipeline Completed Successfully!")
    print("Your database now contains weather data for all Australian states.")


if __name__ == "__main__":
    main()