"""
Enhanced models for Australian Bureau of Meteorology (BOM) weather data
Extends the existing weather database with BOM-specific data structures
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from src.database.connection import Base
import datetime

class BOMWeatherStation(Base):
    """Extended weather station model for BOM data"""
    __tablename__ = 'bom_weather_stations'
    
    id = Column(Integer, primary_key=True)
    station_name = Column(String(255), nullable=False, index=True)
    station_code = Column(String(50), unique=True, index=True)  # Derived from filename
    state = Column(String(50))
    country = Column(String(100), default='Australia')
    
    # Geographic data
    location = Column(Geometry('POINT', srid=4326))  # Will be populated later
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    data_source = Column(String(50), default='BOM')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    weather_records = relationship("BOMWeatherData", back_populates="station")
    
    def __repr__(self):
        return f"<BOMWeatherStation(name='{self.station_name}', code='{self.station_code}')>"

class BOMWeatherData(Base):
    """Daily weather data from Bureau of Meteorology"""
    __tablename__ = 'bom_weather_data'
    
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('bom_weather_stations.id'), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    
    # Evapotranspiration data
    evapotranspiration_mm = Column(Float)  # Daily evapotranspiration (mm) 0000-2400
    
    # Precipitation data
    rainfall_mm = Column(Float)  # Rain (mm) 0900-0900
    pan_evaporation_mm = Column(Float)  # Pan evaporation (mm) 0900-0900
    
    # Temperature data (°C)
    max_temperature = Column(Float)
    min_temperature = Column(Float)
    
    # Humidity data (%)
    max_relative_humidity = Column(Float)
    min_relative_humidity = Column(Float)
    
    # Wind data
    wind_speed_ms = Column(Float)  # Average 10m wind speed (m/sec)
    
    # Solar radiation
    solar_radiation_mj = Column(Float)  # Solar radiation (MJ/sq m)
    
    # Data quality and metadata
    data_source = Column(String(50), default='BOM')
    file_source = Column(String(255))  # Original filename
    quality_flags = Column(Text)  # For storing any quality indicators
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    station = relationship("BOMWeatherStation", back_populates="weather_records")
    
    # Constraints and indexes
    __table_args__ = (
        # Unique constraint to prevent duplicate records
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<BOMWeatherData(station_id={self.station_id}, date={self.observation_date}, temp={self.max_temperature}°C)>"

class BOMDataIngestionLog(Base):
    """Log of data ingestion processes"""
    __tablename__ = 'bom_ingestion_log'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    station_name = Column(String(255))
    ingestion_start = Column(DateTime, nullable=False)
    ingestion_end = Column(DateTime)
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    status = Column(String(20))  # 'success', 'failed', 'partial'
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<BOMDataIngestionLog(file='{self.filename}', status='{self.status}', records={self.records_inserted})>"
