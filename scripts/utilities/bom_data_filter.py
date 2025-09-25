"""
BOM Data Filter - Database-driven filtering for Bureau of Meteorology data

CODE REVIEW SUMMARY:
✅ GOOD PRACTICES:
- Good separation of concerns with dedicated filter class
- Proper database session management with try/finally blocks
- Comprehensive error handling and encoding detection
- Well-structured methods for different filtering operations
- Good use of SQLAlchemy ORM for complex queries
- Proper type hints throughout

⚠️ AREAS FOR IMPROVEMENT:
- Some methods are quite long and could be broken down
- Missing comprehensive input validation
- Could benefit from more efficient database queries
- Some hardcoded values that could be configurable
- Missing unit tests
- No logging for debugging/troubleshooting

🔧 RECOMMENDATIONS:
- Add comprehensive logging throughout the class
- Implement input validation and sanitization
- Add unit tests for all public methods
- Consider using async database operations
- Add caching for frequently accessed data
- Implement proper error handling with custom exceptions
- Add performance monitoring and query optimization
- Consider using pandas more efficiently for data processing
"""

import pandas as pd
import os
from pathlib import Path
import glob
from typing import List, Optional, Dict, Any, Tuple
import json
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_, or_, func, text
from app.database.models import BOMWeatherStation, BOMWeatherData
from app.database.connection import get_database_url

def detect_file_encoding(file_path: Path) -> str:
    """Detect the encoding of a file by trying different encodings"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # Try to read first 1KB
            return encoding
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, return utf-8 with error replacement
    return 'utf-8'

class BOMDataFilter:
    def __init__(self):
        # Database connection
        self.engine = create_engine(get_database_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_available_locations(self) -> List[str]:
        """Get list of all available locations from database"""
        session = self.SessionLocal()
        try:
            # Get distinct station names from the database
            result = session.query(BOMWeatherStation.station_name).distinct().all()
            locations = [row[0] for row in result if row[0]]
            return sorted(locations)
        finally:
            session.close()

    def get_available_variables(self, sample_location: Optional[str] = None) -> List[str]:
        """Get list of available weather variables from database"""
        session = self.SessionLocal()
        try:
            # Query to get non-null columns from BOM weather data
            query = session.query(
                func.count(BOMWeatherData.evapotranspiration_mm).label('et_count'),
                func.count(BOMWeatherData.rain_mm).label('rain_count'),
                func.count(BOMWeatherData.max_temperature_c).label('max_temp_count'),
                func.count(BOMWeatherData.min_temperature_c).label('min_temp_count'),
                func.count(BOMWeatherData.max_relative_humidity_pct).label('max_humidity_count'),
                func.count(BOMWeatherData.min_relative_humidity_pct).label('min_humidity_count'),
                func.count(BOMWeatherData.wind_speed_m_per_sec).label('wind_count'),
                func.count(BOMWeatherData.solar_radiation_mj_per_sq_m).label('solar_count')
            )
            
            if sample_location:
                # Filter by location if specified
                station = session.query(BOMWeatherStation).filter(
                    BOMWeatherStation.station_name.ilike(f'%{sample_location}%')
                ).first()
                if station:
                    query = query.filter(BOMWeatherData.station_id == station.id)
            
            result = query.first()
            
            available_vars = []
            if result.et_count > 0:
                available_vars.append('evapotranspiration')
            if result.rain_count > 0:
                available_vars.append('rainfall')
            if result.max_temp_count > 0 or result.min_temp_count > 0:
                available_vars.append('temperature')
            if result.max_humidity_count > 0 or result.min_humidity_count > 0:
                available_vars.append('humidity')
            if result.wind_count > 0:
                available_vars.append('wind_speed')
            if result.solar_count > 0:
                available_vars.append('solar_radiation')
            
            return available_vars
        finally:
            session.close()

    def filter_data(self,
                   locations: Optional[List[str]] = None,
                   variables: Optional[List[str]] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   output_format: str = 'dataframe') -> Any:
        """
        Filter BOM data by location, variables, and date range using database queries

        Args:
            locations: List of location names to filter
            variables: List of weather variables to include
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            output_format: 'dataframe', 'json', or 'csv'

        Returns:
            Filtered data in specified format
        """
        session = self.SessionLocal()
        try:
            # Build the base query
            query = session.query(BOMWeatherData)

            # Apply location filter
            if locations:
                location_filters = []
                for location in locations:
                    location_filters.append(BOMWeatherData.station_name.ilike(f'%{location}%'))
                query = query.filter(or_(*location_filters))

            # Apply date filters
            if start_date:
                query = query.filter(BOMWeatherData.date >= start_date)
            if end_date:
                query = query.filter(BOMWeatherData.date <= end_date)

            # Execute query and get results
            results = query.all()

            # Convert to the desired format
            if output_format == 'dataframe':
                return self._results_to_dataframe(results, variables)
            elif output_format == 'json':
                return self._results_to_json(results, variables)
            elif output_format == 'csv':
                return self._results_to_csv(results, variables)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        finally:
            session.close()

    def _results_to_dataframe(self, results, variables=None):
        """Convert query results to pandas DataFrame"""
        data = []
        for record in results:
            row = {
                'date': record.date.isoformat() if record.date else None,
                'location': record.station_name,
                'latitude': None,  # Will be populated from station data if needed
                'longitude': None,  # Will be populated from station data if needed
            }
            
            # Add weather variables based on what's requested
            if not variables or 'evapotranspiration' in variables:
                row['evapotranspiration'] = record.evapotranspiration_mm
            if not variables or 'rainfall' in variables:
                row['rainfall'] = record.rain_mm
            if not variables or 'temperature' in variables:
                row['max_temperature'] = record.max_temperature_c
                row['min_temperature'] = record.min_temperature_c
            if not variables or 'humidity' in variables:
                row['max_humidity'] = record.max_relative_humidity_pct
                row['min_humidity'] = record.min_relative_humidity_pct
            if not variables or 'wind_speed' in variables:
                row['wind_speed'] = record.wind_speed_m_per_sec
            if not variables or 'solar_radiation' in variables:
                row['solar_radiation'] = record.solar_radiation_mj_per_sq_m
            
            data.append(row)
        
        return pd.DataFrame(data)

    def _results_to_json(self, results, variables=None):
        """Convert query results to JSON"""
        df = self._results_to_dataframe(results, variables)
        return df.to_json(orient='records', date_format='iso')

    def _results_to_csv(self, results, variables=None):
        """Convert query results to CSV string"""
        df = self._results_to_dataframe(results, variables)
        return df.to_csv(index=False)

    def get_location_summary(self, location: str) -> Dict[str, Any]:
        """Get summary statistics for a specific location from database"""
        session = self.SessionLocal()
        try:
            # Find the station
            station = session.query(BOMWeatherStation).filter(
                BOMWeatherStation.station_name.ilike(f'%{location}%')
            ).first()
            
            if not station:
                return {"error": f"No station found for location: {location}"}
            
            # Get data summary
            result = session.query(
                func.count(BOMWeatherData.id).label('total_records'),
                func.min(BOMWeatherData.date).label('start_date'),
                func.max(BOMWeatherData.date).label('end_date'),
                func.avg(BOMWeatherData.evapotranspiration_mm).label('avg_et'),
                func.avg(BOMWeatherData.rain_mm).label('avg_rainfall'),
                func.avg(BOMWeatherData.max_temperature_c).label('avg_max_temp'),
                func.avg(BOMWeatherData.min_temperature_c).label('avg_min_temp'),
                func.avg(BOMWeatherData.max_relative_humidity_pct).label('avg_max_humidity'),
                func.avg(BOMWeatherData.min_relative_humidity_pct).label('avg_min_humidity'),
                func.avg(BOMWeatherData.wind_speed_m_per_sec).label('avg_wind_speed'),
                func.avg(BOMWeatherData.solar_radiation_mj_per_sq_m).label('avg_solar_radiation')
            ).filter(BOMWeatherData.station_name == station.station_name).first()
            
            if result.total_records == 0:
                return {"error": f"No data found for location: {location}"}
            
            # Build available variables list
            available_variables = []
            if result.avg_et is not None:
                available_variables.append('evapotranspiration')
            if result.avg_rainfall is not None:
                available_variables.append('rainfall')
            if result.avg_max_temp is not None or result.avg_min_temp is not None:
                available_variables.append('temperature')
            if result.avg_max_humidity is not None or result.avg_min_humidity is not None:
                available_variables.append('humidity')
            if result.avg_wind_speed is not None:
                available_variables.append('wind_speed')
            if result.avg_solar_radiation is not None:
                available_variables.append('solar_radiation')
            
            summary = {
                "location": station.station_name,
                "total_records": result.total_records,
                "date_range": {
                    "start": result.start_date.isoformat() if result.start_date else None,
                    "end": result.end_date.isoformat() if result.end_date else None
                },
                "available_variables": available_variables,
                "coordinates": {
                    "latitude": station.latitude,
                    "longitude": station.longitude
                }
            }
            
            # Add statistics
            statistics = {}
            if result.avg_et is not None:
                statistics['evapotranspiration'] = {"mean": round(result.avg_et, 2)}
            if result.avg_rainfall is not None:
                statistics['rainfall'] = {"mean": round(result.avg_rainfall, 2)}
            if result.avg_max_temp is not None:
                statistics['max_temperature'] = {"mean": round(result.avg_max_temp, 2)}
            if result.avg_min_temp is not None:
                statistics['min_temperature'] = {"mean": round(result.avg_min_temp, 2)}
            if result.avg_max_humidity is not None:
                statistics['max_humidity'] = {"mean": round(result.avg_max_humidity, 2)}
            if result.avg_min_humidity is not None:
                statistics['min_humidity'] = {"mean": round(result.avg_min_humidity, 2)}
            if result.avg_wind_speed is not None:
                statistics['wind_speed'] = {"mean": round(result.avg_wind_speed, 2)}
            if result.avg_solar_radiation is not None:
                statistics['solar_radiation'] = {"mean": round(result.avg_solar_radiation, 2)}
            
            if statistics:
                summary["statistics"] = statistics
            
            return summary
            
        finally:
            session.close()

# Example usage
if __name__ == "__main__":
    filter = BOMDataFilter()

    # Get available locations and variables
    locations = filter.get_available_locations()
    variables = filter.get_available_variables()

    print(f"Available locations: {locations[:5]}...")  # Show first 5
    print(f"Available variables: {variables}")

    # Filter for specific location and temperature data
    if locations and 'temperature' in [v.lower() for v in variables]:
        filtered_data = filter.filter_data(
            locations=[locations[0]],  # First location
            variables=['temperature'],
            output_format='dataframe'
        )

        if filtered_data is not None:
            print(f"\nFiltered data shape: {filtered_data.shape}")
            print(f"Sample data:\n{filtered_data.head()}")

        # Get location summary
        summary = filter.get_location_summary(locations[0])
        print(f"\nLocation summary: {json.dumps(summary, indent=2)}")