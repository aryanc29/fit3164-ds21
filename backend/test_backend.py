import requests
import json

# Test if backend is running
backend_url = "http://127.0.0.1:8001"

try:
    # Test health endpoint
    response = requests.get(f"{backend_url}/health")
    print(f"Health check: {response.status_code}")
    if response.status_code == 200:
        print(f"Health response: {response.json()}")
    
    # Test stations endpoint
    response = requests.get(f"{backend_url}/stations")
    print(f"Stations: {response.status_code}")
    if response.status_code == 200:
        stations = response.json()
        print(f"Found {len(stations)} stations")
        if stations:
            print(f"First station: {stations[0]}")
    
    print("✅ Backend is working!")
    
except Exception as e:
    print(f"❌ Backend error: {e}")
