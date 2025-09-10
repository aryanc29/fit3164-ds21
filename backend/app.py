from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5433/weatherdb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="Weather Data Visualization API",
    description="API for visualizing NSW weather station data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class WeatherRecord(BaseModel):
    id: int
    station_name: str
    date: date
    evapotranspiration_mm: Optional[float]
    rain_mm: Optional[float]
    pan_evaporation_mm: Optional[float]
    max_temperature_c: Optional[float]
    min_temperature_c: Optional[float]
    max_relative_humidity_pct: Optional[float]
    min_relative_humidity_pct: Optional[float]
    wind_speed_m_per_sec: Optional[float]
    solar_radiation_mj_per_sq_m: Optional[float]
    file_source: Optional[str]

class StationInfo(BaseModel):
    station_name: str
    record_count: int
    date_range_start: date
    date_range_end: date

class TimeSeriesData(BaseModel):
    date: str
    value: float
    station_name: str

class StationSummary(BaseModel):
    station_name: str
    avg_evapotranspiration: Optional[float]
    avg_rainfall: Optional[float]
    avg_max_temp: Optional[float]
    avg_min_temp: Optional[float]
    total_records: int

# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "Weather Data Visualization API",
        "version": "1.0.0",
        "endpoints": {
            "stations": "/stations",
            "timeseries": "/timeseries",
            "summary": "/summary",
            "compare": "/compare",
            "statistics": "/statistics"
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        result = db.execute(text("SELECT COUNT(*) FROM bom_weather_data"))
        count = result.scalar()
        return {
            "status": "healthy",
            "database_connected": True,
            "total_records": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/stations", response_model=List[StationInfo])
async def get_stations(db: Session = Depends(get_db)):
    """Get all weather stations with their record counts and date ranges"""
    try:
        query = text("""
            SELECT 
                station_name,
                COUNT(*) as record_count,
                MIN(date) as date_range_start,
                MAX(date) as date_range_end
            FROM bom_weather_data 
            GROUP BY station_name
            ORDER BY station_name
        """)
        
        result = db.execute(query)
        stations = []
        
        for row in result:
            stations.append(StationInfo(
                station_name=row.station_name,
                record_count=row.record_count,
                date_range_start=row.date_range_start,
                date_range_end=row.date_range_end
            ))
        
        return stations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stations: {str(e)}")

@app.get("/timeseries")
async def get_timeseries(
    station_name: str = Query(..., description="Name of the weather station"),
    metric: str = Query(..., description="Metric to plot (evapotranspiration_mm, rain_mm, max_temperature_c, min_temperature_c)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get time series data for a specific station and metric"""
    try:
        # Validate metric
        valid_metrics = [
            'evapotranspiration_mm', 'rain_mm', 'pan_evaporation_mm',
            'max_temperature_c', 'min_temperature_c', 'max_relative_humidity_pct',
            'min_relative_humidity_pct', 'wind_speed_m_per_sec', 'solar_radiation_mj_per_sq_m'
        ]
        
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric. Valid options: {valid_metrics}")
        
        # Build query
        where_conditions = ["station_name = :station_name"]
        params = {"station_name": station_name}
        
        if start_date:
            where_conditions.append("date >= :start_date")
            params["start_date"] = start_date
            
        if end_date:
            where_conditions.append("date <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(where_conditions)
        
        query = text(f"""
            SELECT date, {metric} as value, station_name
            FROM bom_weather_data 
            WHERE {where_clause}
              AND {metric} IS NOT NULL
            ORDER BY date
        """)
        
        result = db.execute(query, params)
        
        data = []
        for row in result:
            data.append({
                "date": row.date.isoformat(),
                "value": float(row.value) if row.value is not None else None,
                "station_name": row.station_name
            })
        
        return {
            "station_name": station_name,
            "metric": metric,
            "start_date": start_date,
            "end_date": end_date,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching time series: {str(e)}")

@app.get("/summary", response_model=List[StationSummary])
async def get_station_summary(db: Session = Depends(get_db)):
    """Get summary statistics for all weather stations"""
    try:
        query = text("""
            SELECT 
                station_name,
                AVG(evapotranspiration_mm) as avg_evapotranspiration,
                AVG(rain_mm) as avg_rainfall,
                AVG(max_temperature_c) as avg_max_temp,
                AVG(min_temperature_c) as avg_min_temp,
                COUNT(*) as total_records
            FROM bom_weather_data 
            GROUP BY station_name
            ORDER BY station_name
        """)
        
        result = db.execute(query)
        summaries = []
        
        for row in result:
            summaries.append(StationSummary(
                station_name=row.station_name,
                avg_evapotranspiration=float(row.avg_evapotranspiration) if row.avg_evapotranspiration else None,
                avg_rainfall=float(row.avg_rainfall) if row.avg_rainfall else None,
                avg_max_temp=float(row.avg_max_temp) if row.avg_max_temp else None,
                avg_min_temp=float(row.avg_min_temp) if row.avg_min_temp else None,
                total_records=row.total_records
            ))
        
        return summaries
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")

@app.get("/compare")
async def compare_stations(
    stations: List[str] = Query(..., description="List of station names to compare"),
    metric: str = Query(..., description="Metric to compare"),
    aggregation: str = Query(default="monthly", description="Aggregation level (daily, weekly, monthly)"),
    db: Session = Depends(get_db)
):
    """Compare multiple stations for a specific metric"""
    try:
        # Validate inputs
        valid_metrics = [
            'evapotranspiration_mm', 'rain_mm', 'pan_evaporation_mm',
            'max_temperature_c', 'min_temperature_c', 'max_relative_humidity_pct',
            'min_relative_humidity_pct', 'wind_speed_m_per_sec', 'solar_radiation_mj_per_sq_m'
        ]
        
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric. Valid options: {valid_metrics}")
        
        # Determine aggregation function
        if aggregation == "daily":
            date_group = "date"
            date_format = "date"
        elif aggregation == "weekly":
            date_group = "DATE_TRUNC('week', date)"
            date_format = "DATE_TRUNC('week', date)"
        elif aggregation == "monthly":
            date_group = "DATE_TRUNC('month', date)"
            date_format = "DATE_TRUNC('month', date)"
        else:
            raise HTTPException(status_code=400, detail="Invalid aggregation. Valid options: daily, weekly, monthly")
        
        # Build query for multiple stations
        station_placeholders = ', '.join([f':station_{i}' for i in range(len(stations))])
        params = {f'station_{i}': station for i, station in enumerate(stations)}
        
        query = text(f"""
            SELECT 
                {date_format} as period,
                station_name,
                AVG({metric}) as avg_value
            FROM bom_weather_data 
            WHERE station_name IN ({station_placeholders})
              AND {metric} IS NOT NULL
            GROUP BY {date_group}, station_name
            ORDER BY period, station_name
        """)
        
        result = db.execute(query, params)
        
        data = {}
        for row in result:
            period = row.period.isoformat() if hasattr(row.period, 'isoformat') else str(row.period)
            if period not in data:
                data[period] = {}
            data[period][row.station_name] = float(row.avg_value) if row.avg_value else None
        
        return {
            "stations": stations,
            "metric": metric,
            "aggregation": aggregation,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing stations: {str(e)}")

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall statistics for the weather dataset"""
    try:
        query = text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT station_name) as total_stations,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                
                -- Evapotranspiration stats
                AVG(evapotranspiration_mm) as avg_et,
                MIN(evapotranspiration_mm) as min_et,
                MAX(evapotranspiration_mm) as max_et,
                STDDEV(evapotranspiration_mm) as std_et,
                
                -- Rainfall stats
                AVG(rain_mm) as avg_rain,
                MIN(rain_mm) as min_rain,
                MAX(rain_mm) as max_rain,
                STDDEV(rain_mm) as std_rain,
                
                -- Temperature stats
                AVG(max_temperature_c) as avg_max_temp,
                MIN(max_temperature_c) as min_max_temp,
                MAX(max_temperature_c) as max_max_temp,
                AVG(min_temperature_c) as avg_min_temp,
                MIN(min_temperature_c) as min_min_temp,
                MAX(min_temperature_c) as max_min_temp
                
            FROM bom_weather_data
        """)
        
        result = db.execute(query)
        row = result.fetchone()
        
        return {
            "dataset_overview": {
                "total_records": row.total_records,
                "total_stations": row.total_stations,
                "earliest_date": row.earliest_date.isoformat() if row.earliest_date else None,
                "latest_date": row.latest_date.isoformat() if row.latest_date else None
            },
            "evapotranspiration": {
                "average": float(row.avg_et) if row.avg_et else None,
                "minimum": float(row.min_et) if row.min_et else None,
                "maximum": float(row.max_et) if row.max_et else None,
                "std_deviation": float(row.std_et) if row.std_et else None
            },
            "rainfall": {
                "average": float(row.avg_rain) if row.avg_rain else None,
                "minimum": float(row.min_rain) if row.min_rain else None,
                "maximum": float(row.max_rain) if row.max_rain else None,
                "std_deviation": float(row.std_rain) if row.std_rain else None
            },
            "temperature": {
                "max_average": float(row.avg_max_temp) if row.avg_max_temp else None,
                "max_minimum": float(row.min_max_temp) if row.min_max_temp else None,
                "max_maximum": float(row.max_max_temp) if row.max_max_temp else None,
                "min_average": float(row.avg_min_temp) if row.avg_min_temp else None,
                "min_minimum": float(row.min_min_temp) if row.min_min_temp else None,
                "min_maximum": float(row.max_min_temp) if row.max_min_temp else None
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@app.get("/monthly-trends")
async def get_monthly_trends(
    metric: str = Query(..., description="Metric to analyze"),
    db: Session = Depends(get_db)
):
    """Get monthly trends across all stations for a specific metric"""
    try:
        valid_metrics = [
            'evapotranspiration_mm', 'rain_mm', 'pan_evaporation_mm',
            'max_temperature_c', 'min_temperature_c', 'max_relative_humidity_pct',
            'min_relative_humidity_pct', 'wind_speed_m_per_sec', 'solar_radiation_mj_per_sq_m'
        ]
        
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric. Valid options: {valid_metrics}")
        
        query = text(f"""
            SELECT 
                EXTRACT(MONTH FROM date) as month,
                EXTRACT(YEAR FROM date) as year,
                AVG({metric}) as avg_value,
                MIN({metric}) as min_value,
                MAX({metric}) as max_value,
                COUNT(*) as record_count
            FROM bom_weather_data 
            WHERE {metric} IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date)
            ORDER BY year, month
        """)
        
        result = db.execute(query)
        
        data = []
        for row in result:
            data.append({
                "year": int(row.year),
                "month": int(row.month),
                "month_name": ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(row.month)],
                "average": float(row.avg_value) if row.avg_value else None,
                "minimum": float(row.min_value) if row.min_value else None,
                "maximum": float(row.max_value) if row.max_value else None,
                "record_count": row.record_count
            })
        
        return {
            "metric": metric,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly trends: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=True)
