"""
Script to populate bom_weather_stations table with stations from bom_weather_data
and add geographical coordinates
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from bom_models import BOMWeatherStation
import datetime

# Create database connection
DATABASE_URL = "postgresql://postgres:password@localhost:5433/weatherdb"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# NSW weather station coordinates
NSW_STATION_COORDINATES = {
    "ALBION PARK (SHELLHARBOUR AIRPORT)": (-34.5600, 150.7870),
    "ALBURY AIRPORT": (-36.0678, 146.9583),
    "ARMIDALE AIRPORT": (-30.5280, 151.6175),
    "BADGERYS CREEK": (-33.8830, 150.7470),
    "BANKSTOWN AIRPORT": (-33.9242, 150.9881),
    "BATHURST AIRPORT": (-33.4094, 149.6522),
    "BELLAMBI": (-34.3667, 150.9283),
    "BEGA": (-36.6833, 149.8333),
    "BROKEN HILL AIRPORT": (-32.0014, 141.4722),
    "CABRAMURRA": (-35.9333, 148.3833),
    "CAMDEN AIRPORT": (-34.0397, 150.6875),
    "CASINO AIRPORT": (-28.8797, 153.0525),
    "COBAR": (-31.4950, 145.8356),
    "COBAR AIRPORT": (-31.5383, 145.7944),
    "COFFS HARBOUR": (-30.3167, 153.1167),
    "COOMA": (-36.2300, 149.1300),
    "COONAMBLE AIRPORT": (-30.9833, 148.3833),
    "DUBBO": (-32.2167, 148.5667),
    "DUBBO AIRPORT": (-32.2167, 148.5667),
    "GOULBURN": (-34.7500, 149.7167),
    "GOSFORD": (-33.4269, 151.3428),
    "GRAFTON": (-29.6833, 152.9333),
    "GRIFFITH AIRPORT": (-34.2489, 146.0672),
    "HUNTER VALLEY": (-32.7833, 151.2167),
    "INVERELL": (-29.7833, 151.1333),
    "KEMPSEY": (-31.0833, 152.8333),
    "LISMORE": (-28.8167, 153.2833),
    "MAITLAND AIRPORT": (-32.7017, 151.4933),
    "MOREE": (-29.5000, 149.8333),
    "MORUYA": (-35.9167, 150.1500),
    "MUDGEE": (-32.5667, 149.6000),
    "NARRABRI": (-30.3167, 149.7833),
    "NARRABRI AIRPORT": (-30.3167, 149.7833),
    "NEWCASTLE": (-32.9167, 151.7833),
    "NOWRA": (-34.8833, 150.6000),
    "ORANGE": (-33.2833, 149.1000),
    "ORANGE AIRPORT": (-33.3814, 149.1322),
    "PARKES": (-33.1333, 148.2500),
    "PARKES AIRPORT": (-33.1333, 148.2500),
    "PORT MACQUARIE": (-31.4333, 152.9000),
    "PORT MACQUARIE AIRPORT": (-31.4333, 152.9000),
    "RICHMOND RAAF": (-33.6000, 150.7833),
    "SYDNEY AIRPORT": (-33.9461, 151.1772),
    "SYDNEY (OBSERVATORY HILL)": (-33.8588, 151.2056),
    "TAMWORTH": (-31.0833, 150.8500),
    "WAGGA WAGGA": (-35.1583, 147.4575),
    "WILLIAMTOWN": (-32.7889, 151.8431),
    "WOLLONGONG": (-34.4167, 150.9000),
    "YOUNG": (-34.3167, 148.3000)
    ,"BALLINA AIRPORT": (-28.8348, 153.5570)
    ,"BOMBALA": (-36.9113, 149.2389)
    ,"BOURKE AIRPORT": (-30.0384, 145.9531)
    ,"BYRON BAY (CAPE BYRON)": (-28.6386, 153.6363)
    ,"CANBERRA AIRPORT": (-34.5606, 150.7903)
    ,"CANTERBURY RACECOURSE": (-33.9070, 151.1156)
    ,"CESSNOCK AIRPORT": (-32.7857, 151.3384)
    ,"COFFS HARBOUR AIRPORT": (-30.3229, 153.1158)
    ,"CONDOBOLIN AIRPORT": (-33.0702, 147.2130)
    ,"COOMA AIRPORT": (-36.2941, 148.9733)
    ,"COONABARABRAN AIRPORT": (-31.3315, 149.2710)
    ,"COORANBONG (LAKE MACQUARIE)": (-33.0758, 151.4540)
    ,"COWRA AIRPORT": (-33.8448, 148.6487)
    ,"DENILIQUIN AIRPORT": (-35.5570, 144.9476)
    ,"FORBES AIRPORT": (-33.3617, 147.9276)
    ,"FOWLERS GAP": (-31.3826, 141.7368)
    ,"GLEN INNES AIRPORT": (-29.6753, 151.6914)
    ,"GOULBURN AIRPORT": (-34.8133, 149.7216)
    ,"GRAFTON AIRPORT": (-29.7503, 153.0320)
    ,"GREEN CAPE": (-37.2067, 149.9878)
    ,"GUNNEDAH AIRPORT": (-30.9574, 150.2491)
    ,"HAY AIRPORT": (-34.5312, 144.8326)
    ,"HOLSWORTHY AERODROME": (-33.9937, 150.9512)
    ,"IVANHOE AERODROME": (-32.8928, 144.3110)
    ,"KEMPSEY AIRPORT": (-31.0723, 152.7686)
    ,"KHANCOBAN": (-36.2147, 148.1338)
    ,"KIAMA (BOMBO HEADLAND)": (-34.6532, 150.8609)
    ,"LISMORE AIRPORT": (-28.8307, 153.2589)
    ,"MANGROVE MOUNTAIN": (-33.3009, 151.1915)
    ,"MERIMBULA AIRPORT": (-36.9078, 149.9016)
    ,"MORUYA AIRPORT": (-35.8935, 150.1470)
    ,"MOSS VALE": (-34.5486, 150.3727)
    ,"MOUNT BOYCE": (-33.6156, 150.2664)
    ,"MOUNT GININI": (-35.5295, 148.7722)
    ,"MUDGEE AIRPORT": (-32.5624, 149.6139)
    ,"NARRANDERA AIRPORT": (-34.7013, 146.5127)
    ,"NERRIGA": (-35.1150, 150.0844)
    ,"NORAH HEAD": (-33.2817, 151.5678)
    ,"NULLO MOUNTAIN": (-32.6652, 150.1846)
    ,"PATERSON (TOCAL)": (-32.7011, 151.5849)
    ,"PENRITH LAKES": (-33.7267, 150.6848)
    ,"PERISHER VALLEY": (-36.4056, 148.4107)
    ,"SCONE AIRPORT": (-32.0376, 150.8320)
    ,"TAMWORTH AIRPORT": (-31.0795, 150.8472)
    ,"TAREE AIRPORT": (-31.8878, 152.5131)
    ,"TEMORA AIRPORT": (-34.4240, 147.5141)
    ,"TERREY HILLS": (-33.6918, 151.2206)
    ,"THREDBO": (-36.5048, 148.3057)
    ,"TIBOOBURRA AIRPORT": (-29.4490, 142.0581)
    ,"TRANGIE RESEARCH STATION": (-31.9759, 147.9563)
    ,"ULLADULLA": (-35.3622, 150.4752)
    ,"WALGETT AIRPORT": (-30.0322, 148.1255)
    ,"WEST WYALONG AIRPORT": (-33.9372, 147.1910)
    ,"WHITE CLIFFS": (-30.8504, 143.0900)
    ,"WILCANNIA AERODROME": (-31.5200, 143.3839)
    ,"WILLIAMTOWN RAAF": (-32.7945, 151.8400)
    ,"YANCO AGRICULTURAL INSTITUTE": (-34.6274, 146.4312)
    ,"YOUNG AIRPORT": (-34.2566, 148.2468)
}

def populate_bom_stations():
    """Populate bom_weather_stations table from unique stations in bom_weather_data"""
    session = Session()
    
    try:
        # Get unique station names from weather data
        result = session.execute(text("""
            SELECT DISTINCT station_name 
            FROM bom_weather_data 
            ORDER BY station_name
        """))

        unique_stations = [row.station_name for row in result]
        print(f"Found {len(unique_stations)} unique stations in weather data")

        # Read existing coordinates before clearing
        existing_coords = {}
        for s in session.query(BOMWeatherStation).all():
            if s.latitude is not None and s.longitude is not None:
                existing_coords[s.station_name.upper().strip()] = (s.latitude, s.longitude)

        # Clear existing stations
        session.execute(text("DELETE FROM bom_weather_stations"))
        session.commit()
        print("Cleared existing station records")

        added_count = 0

        for station_name in unique_stations:
            # Create station code from name (simplified)
            station_code = station_name.replace(" ", "_").replace("(", "").replace(")", "").upper()

            # Get coordinates: prefer existing, then static dict
            lat, lon = None, None
            station_key = station_name.upper().strip()
            if station_key in existing_coords:
                lat, lon = existing_coords[station_key]
                print(f"🟢 {station_name}: (from DB) ({lat}, {lon})")
            elif station_key in NSW_STATION_COORDINATES:
                lat, lon = NSW_STATION_COORDINATES[station_key]
                print(f"✅ {station_name}: (from dict) ({lat}, {lon})")
            else:
                print(f"❌ {station_name}: No coordinates found")

            # Create station record
            station = BOMWeatherStation(
                station_name=station_name,
                station_code=station_code,
                state="NSW",
                country="Australia",
                latitude=lat,
                longitude=lon,
                is_active=True,
                data_source="BOM",
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )

            session.add(station)
            added_count += 1
        
        # Commit all changes
        session.commit()
        print(f"\n🎉 Successfully added {added_count} stations to bom_weather_stations")
        
        # Show summary
        total_stations = session.query(BOMWeatherStation).count()
        stations_with_coords = session.query(BOMWeatherStation).filter(
            BOMWeatherStation.latitude.isnot(None),
            BOMWeatherStation.longitude.isnot(None)
        ).count()
        
        print(f"\n📊 SUMMARY:")
        print(f"Total stations: {total_stations}")
        print(f"Stations with coordinates: {stations_with_coords}")
        print(f"Coverage: {(stations_with_coords/total_stations)*100:.1f}%")
        
        return added_count
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error populating stations: {e}")
        return 0
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Populating BOM weather stations...")
    populate_bom_stations()
    print("✨ Done!")
