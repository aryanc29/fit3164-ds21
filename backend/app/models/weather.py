from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
from datetime import datetime

from app.core.database import Base


class WeatherStation(Base):
    """Weather station model"""
    __tablename__ = "weather_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    state = Column(String(50))
    country = Column(String(100), default="Australia")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float)  # meters above sea level
    location = Column(Geometry("POINT", srid=4326))  # PostGIS geometry
    
    # Metadata
    source = Column(String(50), nullable=False)  # BOM, Meteostat, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    observations = relationship("WeatherObservation", back_populates="station", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WeatherStation(station_id='{self.station_id}', name='{self.name}')>"


class WeatherObservation(Base):
    """Weather observation model"""
    __tablename__ = "weather_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(UUID(as_uuid=True), ForeignKey("weather_stations.id"), nullable=False)
    
    # Temporal data
    observation_time = Column(DateTime, nullable=False, index=True)
    local_time = Column(DateTime)
    
    # Temperature (Celsius)
    temperature = Column(Float)
    apparent_temperature = Column(Float)
    temperature_min = Column(Float)
    temperature_max = Column(Float)
    dew_point = Column(Float)
    
    # Pressure (hPa)
    pressure_msl = Column(Float)  # Mean sea level pressure
    pressure_station = Column(Float)  # Station pressure
    
    # Humidity (%)
    humidity = Column(Float)
    
    # Wind
    wind_speed = Column(Float)  # km/h
    wind_direction = Column(Float)  # degrees
    wind_gust = Column(Float)  # km/h
    
    # Precipitation (mm)
    rainfall_1h = Column(Float)
    rainfall_24h = Column(Float)
    rainfall_since_9am = Column(Float)
    
    # Visibility (km)
    visibility = Column(Float)
    
    # Cloud cover (oktas 0-8)
    cloud_cover = Column(Float)
    
    # Weather conditions
    weather_description = Column(String(200))
    weather_code = Column(String(20))
    
    # Solar radiation (MJ/m²)
    solar_radiation = Column(Float)
    
    # UV Index
    uv_index = Column(Float)
    
    # Data quality indicators
    data_quality = Column(String(20), default="good")  # good, fair, poor
    is_estimated = Column(Boolean, default=False)
    
    # Metadata
    source = Column(String(50), nullable=False)
    raw_data = Column(Text)  # Store original API response
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    station = relationship("WeatherStation", back_populates="observations")

    def __repr__(self):
        return f"<WeatherObservation(station_id='{self.station_id}', time='{self.observation_time}')>"


class UserDataset(Base):
    """User-uploaded dataset model"""
    __tablename__ = "user_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(20))
    
    # Dataset metadata
    title = Column(String(200))
    description = Column(Text)
    total_records = Column(Integer)
    processed_records = Column(Integer)
    
    # Processing status
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, failed
    processing_log = Column(Text)
    error_message = Column(Text)
    
    # Temporal range
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    
    # Spatial bounds
    bbox_north = Column(Float)
    bbox_south = Column(Float)
    bbox_east = Column(Float)
    bbox_west = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="datasets")
    observations = relationship("UserObservation", back_populates="dataset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserDataset(filename='{self.filename}', status='{self.status}')>"


class UserObservation(Base):
    """User-uploaded weather observation"""
    __tablename__ = "user_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("user_datasets.id"), nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    location_name = Column(String(200))
    
    # Temporal
    observation_time = Column(DateTime, nullable=False, index=True)
    
    # Weather data (same structure as WeatherObservation but nullable)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    rainfall = Column(Float)
    
    # Additional custom fields from user data
    custom_fields = Column(Text)  # JSON string for flexible schema
    
    # Data validation
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(Text)
    
    # Metadata
    row_number = Column(Integer)  # Original row in uploaded file
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dataset = relationship("UserDataset", back_populates="observations")

    def __repr__(self):
        return f"<UserObservation(dataset_id='{self.dataset_id}', time='{self.observation_time}')>"
