#!/usr/bin/env python3
"""
Test script to download BOM weather data for a single state (NSW)
"""

import datetime
import time
from ftplib import FTP
import pandas as pd
import io
import os
import socket
from dateutil.relativedelta import relativedelta

username = 'anonymous'
password = 'gakoven109@futurejs.com'

# Configure socket timeout globally
socket.setdefaulttimeout(30)  # 30 second timeout

## Set start and end time, to filter last 12 months files
today = datetime.datetime.now()

# Fix: Calculate proper date range for PAST 12 months
endtime = today.replace(day=1) - datetime.timedelta(days=1)  # End of last month
starttime = endtime.replace(day=1) - relativedelta(months=11)  # Start of 12 months ago

# Generate list of YYYY-MM dates using proper month arithmetic
date_list = []
current_date = starttime
while current_date <= endtime:
    date_list.append(current_date.strftime('%Y%m'))
    current_date += relativedelta(months=1)  # Properly add one month

print("List of YYYY-MM dates between start and end time:")
print(date_list)

# Connect to the FTP server to get list of location in NSW
def get_observation_location(ftp_server, ftp_directory):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to {ftp_server} (attempt {attempt + 1}/{max_retries})")
            with FTP(ftp_server, timeout=30) as ftp:
                ftp.login(username, password)
                ftp.cwd(ftp_directory)

                # Get list of directories in the current directory
                observe_locations_list = ftp.nlst()
                print(f"Successfully retrieved {len(observe_locations_list)} locations")
                return observe_locations_list

        except (TimeoutError, ConnectionError, OSError, socket.timeout) as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Shorter backoff
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Failed to connect after {max_retries} attempts")
                return []

# Function to download files from FTP server
def download_files_from_ftp(ftp_server, ftp_directory, local_directory, observe_location, date_list):
    # Create local directory if it doesn't exist
    os.makedirs(local_directory, exist_ok=True)

    max_retries = 3
    success = False

    for attempt in range(max_retries):
        try:
            print(f"  Connecting to FTP server (attempt {attempt + 1}/{max_retries})")
            with FTP(ftp_server, timeout=30) as ftp:
                ftp.login(username, password)
                ftp_directory_location = ftp_directory + observe_location + '/'

                try:
                    ftp.cwd(ftp_directory_location)
                    print(f"  Successfully accessed directory: {ftp_directory_location}")
                except Exception as e:
                    print(f"  Could not access directory for {observe_location}: {e}")
                    return False

                filenames = [f"{observe_location}-{date}" for date in date_list]
                downloaded_count = 0

                for filename in filenames:
                    remote_filepath = f"{filename}.csv"
                    local_filepath = f"{local_directory}/{filename}.csv"

                    # Skip if file already exists
                    if os.path.exists(local_filepath):
                        print(f"    File '{remote_filepath}' already exists, skipping...")
                        continue

                    try:
                        with open(local_filepath, "wb") as local_file:
                            ftp.retrbinary(f"RETR {remote_filepath}", local_file.write)
                            print(f"    Downloaded: {remote_filepath}")
                            downloaded_count += 1

                    except Exception as e:
                        print(f"    File not available: {remote_filepath} ({e})")

                print(f"  Successfully downloaded {downloaded_count} files for {observe_location}")
                return True  # Success

        except (TimeoutError, ConnectionError, OSError, socket.timeout) as e:
            print(f"  Connection attempt {attempt + 1} failed for {observe_location}: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3  # Shorter backoff
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"  Failed to process {observe_location} after {max_retries} attempts")
                return False

def main():
    """Main function to test download for NSW only"""
    print("🌤️  BOM Weather Data Test Download - NSW Only")
    print("=" * 60)

    state_code = 'nsw'
    ftp_server = "ftp.bom.gov.au"
    base_ftp_directory = "/anon/gen/clim_data/IDCKWCDEA0/tables/"
    ftp_directory = f"{base_ftp_directory}{state_code}/"
    local_directory = "./data/bom_data"

    print(f"Processing state: {state_code.upper()}")
    print(f"FTP Directory: {ftp_directory}")

    # Get observation locations from FTP server for NSW
    print("Fetching observation locations...")
    observe_locations = get_observation_location(ftp_server, ftp_directory)

    if not observe_locations:
        print("Could not retrieve observation locations. Exiting.")
        return False

    # Download files from FTP server for first 3 locations only (for testing)
    print(f"\nFound {len(observe_locations)} observation locations")
    print("Testing with first 3 locations only...")

    successful_downloads = 0
    failed_downloads = 0

    # Test with just the first 3 locations
    test_locations = observe_locations[:3]

    for i, observe_location in enumerate(test_locations, 1):
        print(f"\nProcessing location {i}/{len(test_locations)}: {observe_location}")

        success = download_files_from_ftp(ftp_server, ftp_directory, local_directory, observe_location, date_list)

        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1

        # Add a pause between locations
        if i < len(test_locations):
            print("  Waiting 2 seconds before next location...")
            time.sleep(2)

    print("\nTest completed!")
    print(f"Successfully processed: {successful_downloads} locations")
    print(f"Failed to process: {failed_downloads} locations")

    # Check downloaded files
    if os.path.exists(local_directory):
        csv_files = [f for f in os.listdir(local_directory) if f.endswith('.csv')]
        print(f"Total CSV files in directory: {len(csv_files)}")

        if csv_files:
            print("Sample files:")
            for csv_file in csv_files[:5]:
                file_path = os.path.join(local_directory, csv_file)
                file_size = os.path.getsize(file_path)
                print(f"  - {csv_file} ({file_size} bytes)")

    return successful_downloads > 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Test successful! The download process is working.")
        print("You can now run the full download script for all states.")
    else:
        print("\n❌ Test failed. Please check your internet connection and FTP access.")