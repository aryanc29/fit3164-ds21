#!/usr/bin/env python3
"""
Simple FTP connectivity test for BOM server
Run this to check if the FTP server is accessible
"""

import socket
from ftplib import FTP
import time

def test_ftp_connection():
    ftp_server = "ftp.bom.gov.au"
    username = 'anonymous'
    password = 'gakoven109@futurejs.com'
    
    print(f"Testing FTP connection to {ftp_server}")
    print("=" * 50)
    
    # Test 1: Basic socket connection
    print("1. Testing basic socket connection...")
    try:
        sock = socket.create_connection((ftp_server, 21), timeout=30)
        sock.close()
        print("   ✓ Socket connection successful")
    except Exception as e:
        print(f"   ✗ Socket connection failed: {e}")
        return False
    
    # Test 2: FTP connection
    print("2. Testing FTP connection...")
    try:
        ftp = FTP(ftp_server, timeout=30)
        print("   ✓ FTP connection established")
        
        # Test 3: FTP login
        print("3. Testing FTP login...")
        ftp.login(username, password)
        print("   ✓ FTP login successful")
        
        # Test 4: Directory listing
        print("4. Testing directory access...")
        ftp.cwd("/anon/gen/clim_data/IDCKWCDEA0/tables/nsw/")
        files = ftp.nlst()
        print(f"   ✓ Directory access successful, found {len(files)} items")
        
        # Show first few items
        print("   First few items:")
        for item in files[:5]:
            print(f"     - {item}")
        
        ftp.quit()
        print("\n✓ All tests passed! FTP server is accessible.")
        return True
        
    except Exception as e:
        print(f"   ✗ FTP test failed: {e}")
        return False

def test_network_connectivity():
    """Test general network connectivity"""
    print("\nTesting general network connectivity...")
    
    test_sites = [
        ("google.com", 80),
        ("github.com", 443),
        ("bom.gov.au", 80)
    ]
    
    for site, port in test_sites:
        try:
            sock = socket.create_connection((site, port), timeout=10)
            sock.close()
            print(f"✓ {site}:{port} - accessible")
        except Exception as e:
            print(f"✗ {site}:{port} - {e}")

if __name__ == "__main__":
    print("BOM FTP Connectivity Test")
    print("=" * 30)
    
    # Test network first
    test_network_connectivity()
    
    # Wait a moment
    time.sleep(2)
    
    # Test FTP
    success = test_ftp_connection()
    
    if not success:
        print("\nTroubleshooting suggestions:")
        print("1. Check your internet connection")
        print("2. Try running the script at a different time")
        print("3. Check if your firewall/antivirus is blocking FTP")
        print("4. Try using a VPN if you're on a restricted network")
        print("5. Consider using the HTTP alternative method")
