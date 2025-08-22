from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import structlog

from app.services.hybrid_api import hybrid_api

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/test/geocode")
async def test_geocode(
    address: str = Query(..., description="Address to geocode"),
    source: Optional[str] = Query(None, description="Preferred source: google or nominatim")
):
    """Test geocoding functionality"""
    try:
        if source == "google":
            result = await hybrid_api._google_geocode(address)
        elif source == "nominatim":
            result = await hybrid_api._nominatim_geocode(address)
        else:
            result = await hybrid_api.geocode_address(address)
        
        if result:
            return {
                "success": True,
                "data": result,
                "message": f"Successfully geocoded: {address}"
            }
        else:
            raise HTTPException(status_code=404, detail="Address not found")
            
    except Exception as e:
        logger.error("Geocoding test failed", error=str(e), address=address)
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


@router.get("/test/weather")
async def test_weather(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude")
):
    """Test weather data retrieval"""
    try:
        result = await hybrid_api.get_weather_data(lat, lng)
        
        if result:
            return {
                "success": True,
                "data": result,
                "message": f"Weather data retrieved for {lat}, {lng}"
            }
        else:
            raise HTTPException(status_code=404, detail="Weather data not available")
            
    except Exception as e:
        logger.error("Weather test failed", error=str(e), lat=lat, lng=lng)
        raise HTTPException(status_code=500, detail=f"Weather data failed: {str(e)}")


@router.get("/test/stations")
async def test_weather_stations(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(50, description="Search radius in kilometers")
):
    """Test weather station discovery"""
    try:
        result = await hybrid_api.find_nearby_weather_stations(lat, lng, radius)
        
        return {
            "success": True,
            "data": result,
            "message": f"Found {len(result)} weather stations within {radius}km"
        }
            
    except Exception as e:
        logger.error("Weather stations test failed", error=str(e), lat=lat, lng=lng)
        raise HTTPException(status_code=500, detail=f"Weather stations search failed: {str(e)}")


@router.get("/test/all-apis")
async def test_all_apis():
    """Test all API functionality with sample data"""
    results = {
        "geocoding": {},
        "weather": {},
        "stations": {},
        "summary": {"passed": 0, "total": 3}
    }
    
    # Test geocoding
    try:
        geocode_result = await hybrid_api.geocode_address("Melbourne, Australia")
        results["geocoding"] = {
            "success": bool(geocode_result),
            "data": geocode_result,
            "source": geocode_result.get("source") if geocode_result else None
        }
        if geocode_result:
            results["summary"]["passed"] += 1
    except Exception as e:
        results["geocoding"] = {"success": False, "error": str(e)}
    
    # Test weather (using Melbourne coordinates)
    try:
        weather_result = await hybrid_api.get_weather_data(-37.8136, 144.9631)
        results["weather"] = {
            "success": bool(weather_result),
            "data": weather_result,
            "source": weather_result.get("source") if weather_result else None
        }
        if weather_result:
            results["summary"]["passed"] += 1
    except Exception as e:
        results["weather"] = {"success": False, "error": str(e)}
    
    # Test weather stations
    try:
        stations_result = await hybrid_api.find_nearby_weather_stations(-37.8136, 144.9631, 50)
        results["stations"] = {
            "success": True,
            "data": stations_result,
            "count": len(stations_result)
        }
        results["summary"]["passed"] += 1
    except Exception as e:
        results["stations"] = {"success": False, "error": str(e)}
    
    # Overall summary
    results["summary"]["success"] = results["summary"]["passed"] == results["summary"]["total"]
    results["message"] = f"API Tests: {results['summary']['passed']}/{results['summary']['total']} passed"
    
    return results


@router.get("/test/google-status")
async def test_google_status():
    """Check if Google APIs are available and working"""
    status = {
        "google_api_key": bool(hybrid_api.google_available),
        "tests": {}
    }
    
    if hybrid_api.google_available:
        # Test Google Geocoding
        try:
            result = await hybrid_api._google_geocode("Sydney, Australia")
            status["tests"]["geocoding"] = {
                "success": bool(result),
                "data": result
            }
        except Exception as e:
            status["tests"]["geocoding"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Google Places
        try:
            result = await hybrid_api._google_places_weather_stations(-33.8688, 151.2093, 25)
            status["tests"]["places"] = {
                "success": len(result) > 0,
                "count": len(result),
                "data": result[:3]  # First 3 results
            }
        except Exception as e:
            status["tests"]["places"] = {
                "success": False,
                "error": str(e)
            }
    else:
        status["message"] = "Google API key not configured"
    
    return status


@router.get("/test/free-apis")
async def test_free_apis():
    """Test all free APIs"""
    results = {
        "nominatim": {},
        "wttr": {},
        "summary": {"passed": 0, "total": 2}
    }
    
    # Test Nominatim
    try:
        geocode_result = await hybrid_api._nominatim_geocode("Brisbane, Australia")
        results["nominatim"] = {
            "success": bool(geocode_result),
            "data": geocode_result
        }
        if geocode_result:
            results["summary"]["passed"] += 1
    except Exception as e:
        results["nominatim"] = {"success": False, "error": str(e)}
    
    # Test wttr.in weather
    try:
        weather_result = await hybrid_api._get_wttr_weather(-27.4698, 153.0251)  # Brisbane
        results["wttr"] = {
            "success": bool(weather_result),
            "data": weather_result
        }
        if weather_result:
            results["summary"]["passed"] += 1
    except Exception as e:
        results["wttr"] = {"success": False, "error": str(e)}
    
    results["summary"]["success"] = results["summary"]["passed"] == results["summary"]["total"]
    results["message"] = f"Free API Tests: {results['summary']['passed']}/{results['summary']['total']} passed"
    
    return results
