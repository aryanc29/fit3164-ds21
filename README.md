# # Weather Data Visualization Backend

A minimal FastAPI backend for the Interactive Visualisation of Spatial Weather Data project.

## Quick Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys (Secure Method):**
   Instead of using `.env` files, set environment variables directly in your terminal for maximum security:
   
   ```powershell
   # Windows PowerShell - Set your API keys securely
   $env:GOOGLE_MAPS_API_KEY="your-actual-google-maps-api-key-here"
   $env:DATABASE_URL="postgresql://weather_user:weather_pass@localhost:5433/weather_db"
   $env:SECRET_KEY="your-secure-secret-key-here"
   $env:DEBUG="True"
   $env:ACCESS_TOKEN_EXPIRE_MINUTES="30"
   ```
   
   ```bash
   # Linux/macOS - Set your API keys securely
   export GOOGLE_MAPS_API_KEY="your-actual-google-maps-api-key-here"
   export DATABASE_URL="postgresql://weather_user:weather_pass@localhost:5433/weather_db"
   export SECRET_KEY="your-secure-secret-key-here"
   export DEBUG="True"
   export ACCESS_TOKEN_EXPIRE_MINUTES="30"
   ```

3. **Start database services:**
   ```bash
   docker-compose up -d
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## Security Features

- ✅ **No API keys stored in files** - Uses environment variables only
- ✅ **Protected from version control** - No sensitive data in repository
- ✅ **Protected from AI assistants** - API keys not visible in workspace
- ✅ **Runtime verification** - Health check shows API key configuration status

## Project Structure

```
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration and connection
├── models.py            # SQLAlchemy models with PostGIS support
├── init_db.py          # Database initialization script
├── test_spatial.py     # PostGIS spatial functionality tests
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Database services (PostgreSQL + PostGIS + Redis)
├── .env.example        # Environment configuration template (for reference only)
└── README.md           # This file
```

## Database Features

- ✅ **PostgreSQL 15** with **PostGIS 3.3** for spatial data
- ✅ **Weather stations** with geographic coordinates  
- ✅ **Weather data** time-series storage
- ✅ **Spatial regions** for area-based analysis
- ✅ **User locations** with customizable alerts
- ✅ **Geographic queries** (distance, buffers, intersections)
- ✅ **Multiple coordinate systems** (8500+ SRID support)

## Spatial Capabilities

The system can perform advanced spatial operations:
- 📍 Point-based weather station locations
- 📐 Distance calculations between locations  
- 🎯 Buffer zones around points/regions
- 🗺️ Coordinate system transformations
- 🔍 Spatial intersection queries
- 📊 Area-based weather analysis

## Next Steps

This is a minimal setup. You can extend it by adding:
- API endpoints
- Database models
- Authentication
- External API integrations
- Business logic
- Tests