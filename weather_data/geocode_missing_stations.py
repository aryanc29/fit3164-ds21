"""
Geocode missing BOM station coordinates using Nominatim (OpenStreetMap)
"""
import time
import requests
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from bom_models import BOMWeatherStation

DATABASE_URL = "postgresql://postgres:password@localhost:5433/weatherdb"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "fit3164-weather-geocoder/1.0 (your_email@example.com)"


def geocode_station(name):
    params = {
        'q': f'{name}, NSW, Australia',
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': USER_AGENT}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
    return None, None

if __name__ == "__main__":
    session = Session()
    missing = session.query(BOMWeatherStation).filter(
        (BOMWeatherStation.latitude == None) | (BOMWeatherStation.longitude == None)
    ).all()
    print(f"Stations to geocode: {len(missing)}")
    updated = 0
    for s in missing:
        print(f"Geocoding: {s.station_name} ...", end=" ")
        lat, lon = geocode_station(s.station_name)
        if lat and lon:
            s.latitude = lat
            s.longitude = lon
            session.add(s)
            print(f"✅ ({lat:.4f}, {lon:.4f})")
            updated += 1
        else:
            print("❌ Not found")
        time.sleep(1.2)  # Be polite to the API
    session.commit()
    print(f"\nUpdated {updated} stations with coordinates.")
    session.close()
