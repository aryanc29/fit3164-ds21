"""
List all BOM weather stations missing coordinates
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from bom_models import BOMWeatherStation

DATABASE_URL = "postgresql://postgres:password@localhost:5433/weatherdb"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    session = Session()
    missing = session.query(BOMWeatherStation).filter(
        (BOMWeatherStation.latitude == None) | (BOMWeatherStation.longitude == None)
    ).all()
    print(f"Stations missing coordinates: {len(missing)}")
    for s in missing:
        print(s.station_name)
    session.close()
