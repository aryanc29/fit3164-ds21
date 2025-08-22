"""
Hybrid API service combining Google APIs (primary) with free APIs (fallback)
Provides reliable geocoding and weather data with cost optimization
"""

import httpx
import asyncio
import structlog
from typing import Optional, Dict, Any, List, Tuple
from app.core.config import settings

logger = structlog.get_logger(__name__)


class HybridAPIService:
    """Service that intelligently uses Google and free APIs"""
    
    def __init__(self):
        self.google_available = bool(settings.GOOGLE_API_KEY)
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode address using Google first, fallback to Nominatim
        Returns: {lat, lng, formatted_address, source}
        """
        # Try Google Maps first (more accurate, costs money)
        if self.google_available:
            result = await self._google_geocode(address)
            if result:
                logger.info("Geocoding successful", source="google", address=address)
                return result
        
        # Fallback to free Nominatim
        result = await self._nominatim_geocode(address)
        if result:
            logger.info("Geocoding successful", source="nominatim", address=address)
            return result
        
        logger.error("Geocoding failed", address=address)
        return None
    
    async def _google_geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """Google Maps Geocoding API"""
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': settings.GOOGLE_MAPS_API_KEY
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK' and data['results']:
                    result = data['results'][0]
                    location = result['geometry']['location']
                    
                    return {
                        'lat': location['lat'],
                        'lng': location['lng'],
                        'formatted_address': result['formatted_address'],
                        'source': 'google',
                        'accuracy': 'high'
                    }
                else:
                    logger.warning("Google geocoding error", status=data.get('status'))
            else:
                logger.warning("Google geocoding HTTP error", status_code=response.status_code)
                
        except Exception as e:
            logger.error("Google geocoding exception", error=str(e))
        
        return None
    
    async def _nominatim_geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """OpenStreetMap Nominatim geocoding (free)"""
        try:
            # Rate limiting respect
            await asyncio.sleep(1)
            
            url = f"{settings.NOMINATIM_BASE_URL}/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            headers = {
                'User-Agent': settings.USER_AGENT
            }
            
            response = await self.client.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    return {
                        'lat': float(result['lat']),
                        'lng': float(result['lon']),
                        'formatted_address': result['display_name'],
                        'source': 'nominatim',
                        'accuracy': 'medium'
                    }
            else:
                logger.warning("Nominatim HTTP error", status_code=response.status_code)
                
        except Exception as e:
            logger.error("Nominatim geocoding exception", error=str(e))
        
        return None
    
    async def find_nearby_weather_stations(
        self, 
        lat: float, 
        lng: float, 
        radius_km: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find weather stations near coordinates
        Uses Google Places first, fallback to known station list
        """
        
        # Try Google Places first
        if self.google_available:
            stations = await self._google_places_weather_stations(lat, lng, radius_km)
            if stations:
                logger.info("Found weather stations", source="google", count=len(stations))
                return stations
        
        # Fallback to static/database list of known stations
        stations = await self._fallback_weather_stations(lat, lng, radius_km)
        logger.info("Found weather stations", source="fallback", count=len(stations))
        return stations
    
    async def _google_places_weather_stations(
        self, 
        lat: float, 
        lng: float, 
        radius_km: int
    ) -> List[Dict[str, Any]]:
        """Google Places API for weather stations"""
        try:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f'{lat},{lng}',
                'radius': radius_km * 1000,  # Convert to meters
                'keyword': 'weather station OR meteorological OR bureau of meteorology',
                'key': settings.GOOGLE_API_KEY
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    stations = []
                    for place in data.get('results', []):
                        location = place['geometry']['location']
                        stations.append({
                            'name': place['name'],
                            'lat': location['lat'],
                            'lng': location['lng'],
                            'place_id': place['place_id'],
                            'rating': place.get('rating'),
                            'source': 'google_places'
                        })
                    return stations
                else:
                    logger.warning("Google Places error", status=data.get('status'))
            else:
                logger.warning("Google Places HTTP error", status_code=response.status_code)
                
        except Exception as e:
            logger.error("Google Places exception", error=str(e))
        
        return []
    
    async def _fallback_weather_stations(
        self, 
        lat: float, 
        lng: float, 
        radius_km: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback weather stations from known Australian BOM stations
        In production, this would query your database
        """
        
        # Sample known stations (would be from database in production)
        known_stations = [
            {
                'name': 'Melbourne Airport',
                'lat': -37.6734,
                'lng': 144.8433,
                'station_id': '086282',
                'source': 'bom'
            },
            {
                'name': 'Sydney Observatory Hill',
                'lat': -33.8605,
                'lng': 151.2058,
                'station_id': '066062',
                'source': 'bom'
            },
            {
                'name': 'Brisbane',
                'lat': -27.4274,
                'lng': 153.0931,
                'station_id': '040913',
                'source': 'bom'
            },
            {
                'name': 'Adelaide Airport',
                'lat': -34.9524,
                'lng': 138.5204,
                'station_id': '023034',
                'source': 'bom'
            },
            {
                'name': 'Perth Airport',
                'lat': -31.9403,
                'lng': 115.9717,
                'station_id': '009021',
                'source': 'bom'
            }
        ]
        
        # Simple distance calculation (would use PostGIS in production)
        nearby_stations = []
        for station in known_stations:
            # Rough distance calculation
            lat_diff = abs(lat - station['lat'])
            lng_diff = abs(lng - station['lng'])
            rough_distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # Rough km conversion
            
            if rough_distance <= radius_km:
                station['distance_km'] = round(rough_distance, 1)
                nearby_stations.append(station)
        
        return sorted(nearby_stations, key=lambda x: x['distance_km'])
    
    async def get_weather_data(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Get weather data for coordinates
        Uses multiple sources for reliability
        """
        
        # Try free wttr.in first (fast and reliable)
        weather = await self._get_wttr_weather(lat, lng)
        if weather:
            return weather
        
        # Could add OpenWeatherMap here if API key is configured
        # Could add other weather APIs as fallbacks
        
        logger.error("All weather APIs failed", lat=lat, lng=lng)
        return None
    
    async def _get_wttr_weather(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """Get weather from wttr.in (free)"""
        try:
            url = f"{settings.DEMO_WEATHER_URL}/{lat},{lng}?format=j1"
            
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('current_condition', [{}])[0]
                
                if current:
                    return {
                        'temperature': float(current.get('temp_C', 0)),
                        'description': current.get('weatherDesc', [{}])[0].get('value', 'Unknown'),
                        'humidity': int(current.get('humidity', 0)),
                        'wind_speed': float(current.get('windspeedKmph', 0)),
                        'wind_direction': current.get('winddir16Point', 'Unknown'),
                        'pressure': float(current.get('pressure', 0)),
                        'source': 'wttr.in',
                        'updated': current.get('observation_time', 'Unknown')
                    }
            else:
                logger.warning("wttr.in HTTP error", status_code=response.status_code)
                
        except Exception as e:
            logger.error("wttr.in weather exception", error=str(e))
        
        return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
hybrid_api = HybridAPIService()
