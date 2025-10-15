#!/usr/bin/env python3
"""
NSW Weather Dashboard - FastAPI Application
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Optional env loading
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        env_file = Path(__file__).parent.parent / "config" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from: {env_file}")
except ImportError:
    print("Note: python-dotenv not installed. Using system environment variables only.")

# Routers (import after app creation is fine, but do not recreate app later)
try:
    from app.api.download_routes import router as download_router
except Exception as e:
    print(f"Warning: Could not import download_routes: {e}")
    download_router = None

try:
    from app.api.api_routes import router as api_router
except Exception as e:
    print(f"Warning: Could not import api_routes: {e}")
    api_router = None

try:
    from app.auth import auth_routes
except Exception as e:
    print(f"Warning: Could not import auth_routes: {e}")
    auth_routes = None

# Create FastAPI app (once)
app = FastAPI(
    title="NSW Weather Dashboard",
    description="Weather monitoring and analysis dashboard for NSW, Australia",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Routers
if auth_routes:
    app.include_router(auth_routes.router)
if download_router:
    app.include_router(download_router)
if api_router:
    app.include_router(api_router, prefix="/api")

# ---- A11y summary endpoint (used by caption + TTS) ----
@app.get("/summary")
async def summary():
    """
    Returns a short text summary for screen readers and users who prefer text.
    Replace the stub with live stats once available.
    """
    return {
        "text": (
            "This dashboard displays a map of weather stations across Australia. "
            "Use the accessibility panel to enable high-contrast dark mode, "
            "reduce motion and adjust text size. All controls are keyboard accessible."
        )
    }

# ---- Page routes ----
@app.get("/")
async def root():
    """Root endpoint - serve dashboard"""
    dashboard_path = static_path / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"message": "NSW Weather Dashboard API", "status": "running"}

@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint"""
    dashboard_path = static_path / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"message": "Dashboard not found", "status": "error"}

@app.get("/visualisation")
async def weather_visualization():
    """Weather data visualisation page with advanced analytics"""
    viz_path = static_path / "weather_dashboard.html"
    if viz_path.exists():
        return FileResponse(str(viz_path))
    return {"message": "Weather visualisation not found", "status": "error"}

@app.get("/index")
async def test_index():
    """Test index endpoint"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Index page not found", "status": "error"}

@app.get("/analysis")
async def weather_analysis():
    """Alias for weather visualisation page"""
    viz_path = static_path / "weather_visualization.html"
    if viz_path.exists():
        return FileResponse(str(viz_path))
    return {"message": "Weather analysis not found", "status": "error"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "nsw-weather-dashboard"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
