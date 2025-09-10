#!/usr/bin/env python3
"""
Simple test script for our Weather API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(url, description):
    """Test a single API endpoint"""
    try:
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Status: {response.status_code}")
            
            # Print formatted response (limited)
            if isinstance(data, list) and len(data) > 0:
                print(f"   📊 Returned {len(data)} items")
                print(f"   📝 Sample: {json.dumps(data[0], indent=2)[:200]}...")
            elif isinstance(data, dict):
                print(f"   📝 Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   📝 Response: {data}")
        else:
            print(f"   ❌ Error! Status: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error - Server may not be running")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Test all our API endpoints"""
    print("🚀 Testing Weather Visualization API")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏱️ Waiting for server...")
    time.sleep(2)
    
    # Test endpoints
    endpoints = [
        (f"{BASE_URL}/", "Root endpoint"),
        (f"{BASE_URL}/health", "Health check"),
        (f"{BASE_URL}/api/v1/stations", "Get all weather stations"),
        (f"{BASE_URL}/api/v1/weather/recent", "Get recent weather data"),
        (f"{BASE_URL}/api/v1/statistics", "Get weather statistics"),
        (f"{BASE_URL}/api/v1/stations/MEL001", "Get specific station (Melbourne)"),
        (f"{BASE_URL}/api/v1/weather/station/SYD001", "Get weather for Sydney"),
        (f"{BASE_URL}/api/v1/weather/nearby?lat=-37.8136&lng=144.9631&radius_km=50", "Find stations near Melbourne"),
    ]
    
    for url, description in endpoints:
        test_endpoint(url, description)
    
    print(f"\n✅ API Testing Complete!")
    print(f"🌐 Open http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    main()
