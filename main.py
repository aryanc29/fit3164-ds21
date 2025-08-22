from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Weather Data Visualization API",
    description="Backend API for Interactive Visualisation of Spatial Weather Data",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Weather Data Visualization API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if API key is loaded from environment
    api_key_status = "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else "not configured"
    return {
        "status": "healthy", 
        "service": "weather-data-api",
        "api_key_status": api_key_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
