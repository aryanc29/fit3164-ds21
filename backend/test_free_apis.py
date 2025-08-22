#!/usr/bin/env python3
"""
Test script for FREE weather APIs that don't require billing
Tests: BOM (Australia), OpenStreetMap Nominatim, and demo weather
"""

import requests
import json
import time

def test_bom_api():
    """Test Bureau of Meteorology (Australia) - FREE"""
    print("🇦🇺 Testing Bureau of Meteorology API (FREE)...")
    
    # BOM observations for Melbourne
    url = "http://www.bom.gov.au/fwo/IDV60801/IDV60801.95936.json"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', {}).get('data', [])
            
            if observations:
                latest = observations[0]
                temp = latest.get('air_temp')
                name = latest.get('name', 'Unknown')
                time_str = latest.get('local_date_time_full', 'Unknown time')
                
                print(f"✅ BOM API working!")
                print(f"   Station: {name}")
                print(f"   Temperature: {temp}°C" if temp else "   Temperature: Not available")
                print(f"   Time: {time_str}")
                return True
            else:
                print("❌ BOM API: No observation data found")
                return False
        else:
            print(f"❌ BOM API HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ BOM API request failed: {e}")
        return False

def test_nominatim_geocoding():
    """Test OpenStreetMap Nominatim for geocoding - FREE"""
    print("🗺️ Testing OpenStreetMap Nominatim Geocoding (FREE)...")
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': 'Melbourne, Australia',
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'WeatherDataVisualization/1.0 (fit3164-ds21)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                location = data[0]
                lat = location.get('lat')
                lon = location.get('lon')
                display_name = location.get('display_name')
                
                print(f"✅ Nominatim API working!")
                print(f"   Location: {display_name}")
                print(f"   Coordinates: {lat}, {lon}")
                return True
            else:
                print("❌ Nominatim API: No results found")
                return False
        else:
            print(f"❌ Nominatim API HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Nominatim API request failed: {e}")
        return False

def test_demo_weather_api():
    """Test a demo weather API - FREE"""
    print("🌤️ Testing Demo Weather API (FREE)...")
    
    # Using wttr.in - a free weather service
    url = "https://wttr.in/Melbourne?format=j1"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get('current_condition', [{}])[0]
            
            if current:
                temp = current.get('temp_C')
                desc = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
                humidity = current.get('humidity')
                
                print(f"✅ Demo Weather API working!")
                print(f"   Temperature: {temp}°C")
                print(f"   Condition: {desc}")
                print(f"   Humidity: {humidity}%")
                return True
            else:
                print("❌ Demo Weather API: No current condition data")
                return False
        else:
            print(f"❌ Demo Weather API HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Demo Weather API request failed: {e}")
        return False

def test_meteostat_free():
    """Test Meteostat API (requires free signup)"""
    print("📊 Testing Meteostat API (FREE with signup)...")
    
    # Note: This will fail without API key, but shows how to test it
    url = "https://meteostat.p.rapidapi.com/stations/nearby"
    params = {
        'lat': '-37.8136',
        'lon': '144.9631',
        'limit': '5'
    }
    headers = {
        'X-RapidAPI-Key': 'your-rapidapi-key-here',  # Would need actual key
        'X-RapidAPI-Host': 'meteostat.p.rapidapi.com'
    }
    
    # Skip this test for now since we don't have the key
    print("ℹ️ Meteostat requires RapidAPI key (free tier available)")
    print("   Sign up at: https://rapidapi.com/meteostat/api/meteostat/")
    return None

def main():
    """Main test function for FREE APIs"""
    print("🧪 Testing FREE Weather APIs (No Billing Required)")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test free APIs
    if test_bom_api():
        tests_passed += 1
    print()
    
    # Rate limit for Nominatim (1 req/sec)
    time.sleep(1)
    if test_nominatim_geocoding():
        tests_passed += 1
    print()
    
    if test_demo_weather_api():
        tests_passed += 1
    print()
    
    # Show Meteostat info
    test_meteostat_free()
    print()
    
    # Summary
    print("=" * 60)
    print(f"📊 Free API Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All free APIs working! You can start development immediately.")
    elif tests_passed > 0:
        print("✅ Some free APIs working. Good enough to start development!")
    else:
        print("❌ Free APIs failed. Check internet connection.")
    
    print("\n🚀 Next Steps for Your Project:")
    print("1. ✅ Use BOM for Australian weather data (free)")
    print("2. ✅ Use Nominatim for geocoding (free)")
    print("3. 🔄 Sign up for OpenWeatherMap for global data (free tier)")
    print("4. 🔄 Consider Google APIs later for production (requires billing)")
    
    print("\n💡 Development Recommendations:")
    print("- Start with these free APIs for MVP")
    print("- Implement caching to reduce API calls")
    print("- Add rate limiting respect for free services")
    print("- Upgrade to paid APIs when scaling")

if __name__ == "__main__":
    main()
