from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from database import init_db
from api_routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Weather Data Visualization API")
    await init_db()
    yield
    # Shutdown
    print("🛑 Shutting down Weather Data Visualization API")

app = FastAPI(
    title="Weather Data Visualization API",
    description="Backend API for Interactive Visualisation of Spatial Weather Data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1", tags=["weather"])

@app.get("/")
async def root():
    """Serve the frontend"""
    return FileResponse("frontend/index.html")

@app.get("/demo")
async def demo():
    """Alternative route to frontend"""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if API key is loaded from environment
    api_key_status = "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else "not configured"
    db_status = "connected" if os.getenv("DATABASE_URL") else "not configured"
    
    return {
        "status": "healthy", 
        "service": "weather-data-api",
        "api_key_status": api_key_status,
        "database_status": db_status,
        "features": ["PostgreSQL", "PostGIS", "Spatial Data"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
