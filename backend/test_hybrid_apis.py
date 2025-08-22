#!/usr/bin/env python3
"""
Comprehensive API test for both Google APIs (with billing) and Free APIs
Shows hybrid approach for production weather visualization platform
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_maps_geocoding():
    """Test Google Maps Geocoding API (Production)"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY not found")
        return False
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': 'Sydney, Australia',
        'key': api_key
    }
    
    try:
        print("🌍 Testing Google Maps Geocoding (Production)...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                formatted_address = data['results'][0]['formatted_address']
                print(f"✅ Google Geocoding: {formatted_address}")
                print(f"   Coordinates: {location['lat']}, {location['lng']}")
                return True
            else:
                print(f"❌ Google Geocoding error: {data.get('status')}")
                return False
        else:
            print(f"❌ Google Geocoding HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Google Geocoding failed: {e}")
        return False

def test_google_places_nearby():
    """Test Google Places API for weather stations"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found")
        return False
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': '-33.8688,151.2093',  # Sydney coordinates
        'radius': 25000,  # 25km radius
        'keyword': 'weather station',
        'key': api_key
    }
    
    try:
        print("📍 Testing Google Places (Weather Stations)...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                places_count = len(data.get('results', []))
                if places_count > 0:
                    first_place = data['results'][0]
                    print(f"✅ Google Places: Found {places_count} weather stations")
                    print(f"   Example: {first_place.get('name', 'Unknown')}")
                    return True
                else:
                    print("⚠️ Google Places: No weather stations found in area")
                    return True  # API works, just no results
            else:
                print(f"❌ Google Places error: {data.get('status')}")
                return False
        else:
            print(f"❌ Google Places HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Google Places failed: {e}")
        return False

def test_free_geocoding():
    """Test Free Nominatim Geocoding (Backup)"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': 'Brisbane, Australia',
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'WeatherDataVisualization/1.0 (fit3164-ds21)'
    }
    
    try:
        print("🗺️ Testing Free Geocoding (Backup)...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                location = data[0]
                print(f"✅ Free Geocoding: {location.get('display_name')}")
                print(f"   Coordinates: {location.get('lat')}, {location.get('lon')}")
                return True
            else:
                print("❌ Free Geocoding: No results")
                return False
        else:
            print(f"❌ Free Geocoding HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Free Geocoding failed: {e}")
        return False

def test_free_weather():
    """Test Free Weather API"""
    url = "https://wttr.in/Perth?format=j1"
    
    try:
        print("🌤️ Testing Free Weather API...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get('current_condition', [{}])[0]
            
            if current:
                temp = current.get('temp_C')
                desc = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
                print(f"✅ Free Weather: Perth {temp}°C, {desc}")
                return True
            else:
                print("❌ Free Weather: No data")
                return False
        else:
            print(f"❌ Free Weather HTTP error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Free Weather failed: {e}")
        return False

def test_hybrid_approach():
    """Demonstrate hybrid approach: Google for precision, Free for backup"""
    print("🔄 Testing Hybrid Approach...")
    
    # Try Google first, fallback to free
    locations = ['Adelaide, Australia', 'Darwin, Australia']
    
    for location in locations:
        print(f"\n📍 Testing location: {location}")
        
        # Try Google Maps first
        google_success = False
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        if api_key:
            try:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {'address': location, 'key': api_key}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'OK' and data['results']:
                        coords = data['results'][0]['geometry']['location']
                        print(f"   ✅ Google: {coords['lat']}, {coords['lng']}")
                        google_success = True
            except:
                pass
        
        # Fallback to free if Google failed
        if not google_success:
            try:
                time.sleep(1)  # Respect rate limits
                url = "https://nominatim.openstreetmap.org/search"
                params = {'q': location, 'format': 'json', 'limit': 1}
                headers = {'User-Agent': 'WeatherDataVisualization/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        print(f"   🔄 Fallback: {data[0]['lat']}, {data[0]['lon']}")
                    else:
                        print(f"   ❌ Both APIs failed for {location}")
                else:
                    print(f"   ❌ Both APIs failed for {location}")
            except:
                print(f"   ❌ Both APIs failed for {location}")
    
    return True

def main():
    """Test both Google (production) and Free (backup) APIs"""
    print("🧪 Comprehensive API Test - Google + Free APIs")
    print("=" * 60)
    
    # Test Google APIs (Production)
    print("🔷 GOOGLE APIs (Production - Billing Enabled)")
    google_tests = 0
    google_passed = 0
    
    if test_google_maps_geocoding():
        google_passed += 1
    google_tests += 1
    print()
    
    if test_google_places_nearby():
        google_passed += 1
    google_tests += 1
    print()
    
    # Test Free APIs (Backup)
    print("🔶 FREE APIs (Backup - No Billing)")
    free_tests = 0
    free_passed = 0
    
    # Rate limit respect
    time.sleep(1)
    if test_free_geocoding():
        free_passed += 1
    free_tests += 1
    print()
    
    if test_free_weather():
        free_passed += 1
    free_tests += 1
    print()
    
    # Test Hybrid Approach
    print("🔀 HYBRID APPROACH (Production Strategy)")
    test_hybrid_approach()
    print()
    
    # Summary
    print("=" * 60)
    print("📊 RESULTS SUMMARY")
    print(f"Google APIs: {google_passed}/{google_tests} passed")
    print(f"Free APIs: {free_passed}/{free_tests} passed")
    
    if google_passed == google_tests and free_passed == free_tests:
        print("🎉 PERFECT! Both Google and Free APIs working")
        print("🚀 Ready for production with reliable fallbacks")
    elif google_passed > 0 and free_passed > 0:
        print("✅ GOOD! Hybrid approach available")
        print("🔧 Can use Google for precision, Free for backup")
    elif google_passed > 0:
        print("⚠️ Google APIs working, Free APIs need attention")
    elif free_passed > 0:
        print("⚠️ Free APIs working, Google APIs need setup")
    else:
        print("❌ Both API sets failed - check configuration")
    
    print("\n💡 PRODUCTION STRATEGY:")
    print("1. 🎯 Use Google APIs for primary functionality")
    print("2. 🛡️ Use Free APIs as backup/fallback")
    print("3. 💰 Monitor Google API usage and costs")
    print("4. ⚡ Cache results to minimize API calls")
    print("5. 🔄 Implement graceful degradation")

if __name__ == "__main__":
    main()
