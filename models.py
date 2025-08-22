from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime

Base = declarative_base()

class WeatherStation(Base):
    """Weather station model with spatial data"""
    __tablename__ = "weather_stations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    country = Column(String, nullable=False)
    state = Column(String)
    elevation = Column(Float)  # meters above sea level
    
    # PostGIS geometry column for location (Point)
    location = Column(Geometry('POINT', srid=4326))  # WGS84 coordinate system
    
    # Station metadata
    is_active = Column(Boolean, default=True)
    data_source = Column(String)  # BOM, Meteostat, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    weather_data = relationship("WeatherData", back_populates="station")

class WeatherData(Base):
    """Weather data measurements"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Weather measurements
    temperature = Column(Float)  # Celsius
    humidity = Column(Float)     # Percentage
    pressure = Column(Float)     # hPa
    wind_speed = Column(Float)   # km/h
    wind_direction = Column(Float)  # degrees
    precipitation = Column(Float)   # mm
    visibility = Column(Float)      # km
    
    # Weather conditions
    weather_code = Column(String)
    weather_description = Column(Text)
    
    # Data quality and source
    data_source = Column(String, nullable=False)  # API source
    quality_score = Column(Float)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    station = relationship("WeatherStation", back_populates="weather_data")

class SpatialRegion(Base):
    """Spatial regions for weather analysis"""
    __tablename__ = "spatial_regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    region_type = Column(String, nullable=False)  # city, state, country, custom
    
    # PostGIS geometry column for region boundary (Polygon or MultiPolygon)
    boundary = Column(Geometry('MULTIPOLYGON', srid=4326))
    
    # Region metadata
    population = Column(Integer)
    area_km2 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserLocation(Base):
    """User-defined locations for weather tracking"""
    __tablename__ = "user_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # PostGIS geometry column for location (Point)
    location = Column(Geometry('POINT', srid=4326))
    
    # User preferences
    alert_threshold_temp_min = Column(Float)
    alert_threshold_temp_max = Column(Float)
    alert_threshold_precipitation = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
