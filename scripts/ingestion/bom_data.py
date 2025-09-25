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
socket.setdefaulttimeout(60)  # 60 second timeout 

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
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to {ftp_server} (attempt {attempt + 1}/{max_retries})")
            with FTP(ftp_server, timeout=60) as ftp:
                ftp.login(username, password)
                ftp.cwd(ftp_directory)
                
                # Get list of directories in the current directory
                observe_locations_list = ftp.nlst()
                print(f"Successfully retrieved {len(observe_locations_list)} locations")
                return observe_locations_list
                
        except (TimeoutError, ConnectionError, OSError, socket.timeout) as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Failed to connect after {max_retries} attempts")
                return []
    
# Function to download files from FTP server
def download_files_from_ftp(ftp_server, ftp_directory, local_directory, observe_location, date_list):
    # Create local directory if it doesn't exist
    os.makedirs(local_directory, exist_ok=True)
    
    max_retries = 5
    success = False
    
    for attempt in range(max_retries):
        try:
            print(f"  Connecting to FTP server (attempt {attempt + 1}/{max_retries})")
            with FTP(ftp_server, timeout=60) as ftp:
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
                wait_time = (attempt + 1) * 5  # Progressive backoff
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"  Failed to process {observe_location} after {max_retries} attempts")
                return False

state = ['nt','qld','sa','tas','vic','wa']  # Skip NSW for now

ftp_server = "ftp.bom.gov.au"
# ftp_directory will be set dynamically for each state
base_ftp_directory = "/anon/gen/clim_data/IDCKWCDEA0/tables/"

# Define local directory to save files
local_directory = "./data/bom_data"

# Process each state
total_successful_downloads = 0
total_failed_downloads = 0

for state_code in state:
    print(f"\n{'='*60}")
    print(f"Processing state: {state_code.upper()}")
    print(f"{'='*60}")
    
    ftp_directory = f"{base_ftp_directory}{state_code}/"
    
    # Get observation locations from FTP server for this state
    print(f"Fetching observation locations for {state_code.upper()}...")
    observe_locations = get_observation_location(ftp_server, ftp_directory)
    
    if not observe_locations:
        print(f"Could not retrieve observation locations for {state_code.upper()}. Skipping.")
        continue
    
    # Download files from FTP server for this state
    print(f"\nFound {len(observe_locations)} observation locations in {state_code.upper()}")
    successful_downloads = 0
    failed_downloads = 0
    
    for i, observe_location in enumerate(observe_locations, 1):
        print(f"\nProcessing location {i}/{len(observe_locations)} in {state_code.upper()}: {observe_location}")
        
        success = download_files_from_ftp(ftp_server, ftp_directory, local_directory, observe_location, date_list)
        
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        # Add a pause between locations to be respectful to the server
        if i < len(observe_locations):  # Don't sleep after the last location
            print("  Waiting 5 seconds before next location...")
            time.sleep(2)
    
    print(f"\nState {state_code.upper()} completed!")
    print(f"Successfully processed: {successful_downloads} locations")
    print(f"Failed to process: {failed_downloads} locations")
    
    total_successful_downloads += successful_downloads
    total_failed_downloads += failed_downloads
    
    # Add a longer pause between states
    if state_code != state[-1]:  # Don't sleep after the last state
        print("Waiting 30 seconds before next state...")
        time.sleep(30)

print(f"\n{'='*60}")
print("ALL STATES DOWNLOAD PROCESS COMPLETED!")
print(f"{'='*60}")
print(f"Total successfully processed: {total_successful_downloads} locations")
print(f"Total failed to process: {total_failed_downloads} locations")
print(f"Downloaded files are stored in: {local_directory}")