from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import calendar
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.database.connection import get_db
from config import settings

logger = logging.getLogger(__name__)

class WeatherInsightsService:
    """
    Rule-based weather text analysis service
    Follows project patterns: graceful degradation, no external APIs
    """
    
    def __init__(self):
        self.temperature_thresholds = {
            'extreme_hot': 40.0,
            'very_hot': 35.0,
            'hot': 30.0,
            'warm': 25.0,
            'mild': 20.0,
            'cool': 15.0,
            'cold': 10.0,
            'very_cold': 5.0,
            'extreme_cold': 0.0
        }
        
        self.rainfall_categories = {
            'no_rain': (0, 0.1),
            'light': (0.1, 2.5),
            'moderate': (2.5, 10.0),
            'heavy': (10.0, 50.0),
            'very_heavy': (50.0, 100.0),
            'extreme': (100.0, float('inf'))
        }

    async def generate_comprehensive_insights(self, db: Session = None) -> Dict[str, Any]:
        """
        Generate comprehensive weather insights using rule-based analysis
        Follows project pattern: database → analysis → text generation
        """
        if db is None:
            async with get_db() as db:
                return await self._analyze_weather_data(db)
        else:
            return await self._analyze_weather_data(db)

    async def _analyze_weather_data(self, db: Session) -> Dict[str, Any]:
        """Core analysis using PostgreSQL aggregations"""
        try:
            # Get comprehensive weather statistics
            stats = await self._get_weather_statistics(db)
            
            if not stats:
                return self._fallback_insights()
            
            insights = {
                "overview": self._generate_overview_text(stats),
                "temperature_analysis": self._analyze_temperatures(stats),
                "rainfall_analysis": self._analyze_rainfall(stats),
                "seasonal_patterns": self._analyze_seasonal_patterns(stats),
                "extremes_analysis": self._analyze_extremes(stats),
                "station_insights": self._analyze_stations(stats),
                "trends_analysis": self._analyze_trends(stats),
                "recommendations": self._generate_recommendations(stats),
                "_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "data_source": "bom_weather_data",
                    "analysis_method": "rule_based",
                    "record_count": stats.get('overall', {}).get('total_records', 0)
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Weather analysis failed: {e}")
            return self._fallback_insights()

    async def _get_weather_statistics(self, db: Session) -> Optional[Dict]:
        """Get comprehensive statistics from BOM weather data"""
        try:
            query = text("""
                WITH monthly_stats AS (
                    SELECT 
                        EXTRACT(MONTH FROM date) as month,
                        COUNT(*) as records,
                        AVG(max_temperature_c) as avg_max_temp,
                        AVG(min_temperature_c) as avg_min_temp,
                        AVG(rain_mm) as avg_rainfall,
                        MAX(max_temperature_c) as highest_temp,
                        MIN(min_temperature_c) as lowest_temp,
                        MAX(rain_mm) as max_daily_rain,
                        COUNT(DISTINCT station_name) as active_stations
                    FROM bom_weather_data 
                    WHERE max_temperature_c IS NOT NULL 
                    AND min_temperature_c IS NOT NULL
                    GROUP BY EXTRACT(MONTH FROM date)
                ),
                overall_stats AS (
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT station_name) as total_stations,
                        AVG(max_temperature_c) as overall_avg_max,
                        AVG(min_temperature_c) as overall_avg_min,
                        AVG(rain_mm) as overall_avg_rain,
                        MAX(max_temperature_c) as record_high,
                        MIN(min_temperature_c) as record_low,
                        MAX(rain_mm) as record_rainfall,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date
                    FROM bom_weather_data
                ),
                rainfall_dist AS (
                    SELECT 
                        COUNT(CASE WHEN rain_mm = 0 THEN 1 END) as no_rain_days,
                        COUNT(CASE WHEN rain_mm > 0 AND rain_mm <= 2.5 THEN 1 END) as light_rain_days,
                        COUNT(CASE WHEN rain_mm > 2.5 AND rain_mm <= 10 THEN 1 END) as moderate_rain_days,
                        COUNT(CASE WHEN rain_mm > 10 AND rain_mm <= 50 THEN 1 END) as heavy_rain_days,
                        COUNT(CASE WHEN rain_mm > 50 THEN 1 END) as extreme_rain_days,
                        COUNT(*) as total_rain_records
                    FROM bom_weather_data WHERE rain_mm IS NOT NULL
                )
                SELECT 
                    json_build_object(
                        'monthly', (SELECT json_agg(monthly_stats.*) FROM monthly_stats),
                        'overall', (SELECT row_to_json(overall_stats.*) FROM overall_stats),
                        'rainfall_distribution', (SELECT row_to_json(rainfall_dist.*) FROM rainfall_dist)
                    ) as stats
            """)
            
            result = db.execute(query)
            row = result.fetchone()
            
            if row and row.stats:
                return row.stats
                
        except Exception as e:
            logger.error(f"Failed to get weather statistics: {e}")
            
        return None

    def _generate_overview_text(self, stats: Dict) -> str:
        """Generate overview text using rule-based analysis"""
        overall = stats.get('overall', {})
        
        total_records = overall.get('total_records', 0)
        total_stations = overall.get('total_stations', 0)
        avg_max = overall.get('overall_avg_max', 0) or 0
        avg_min = overall.get('overall_avg_min', 0) or 0
        
        # Climate classification based on averages
        climate_desc = self._classify_climate(avg_max, avg_min)
        
        return (
            f"Analysis of {total_records:,} weather records from {total_stations} stations across Australia reveals "
            f"a {climate_desc} climate pattern. The average maximum temperature is {avg_max:.1f}°C, "
            f"while the average minimum is {avg_min:.1f}°C, indicating a daily temperature range of "
            f"{abs(avg_max - avg_min):.1f}°C. This comprehensive dataset provides detailed insights into "
            f"Australia's diverse weather patterns and regional variations."
        )

    def _analyze_temperatures(self, stats: Dict) -> Dict[str, str]:
        """Analyze temperature patterns with rule-based insights"""
        overall = stats.get('overall', {})
        monthly = stats.get('monthly', []) or []
        
        record_high = overall.get('record_high', 0) or 0
        record_low = overall.get('record_low', 0) or 0
        
        # Find hottest and coldest months
        if monthly:
            hottest_month = max(monthly, key=lambda x: x.get('avg_max_temp', 0) or 0)
            coldest_month = min(monthly, key=lambda x: x.get('avg_min_temp', 50) or 50)
            
            hottest_name = calendar.month_name[int(hottest_month.get('month', 1))]
            coldest_name = calendar.month_name[int(coldest_month.get('month', 1))]
        else:
            hottest_name = coldest_name = "Unknown"
            hottest_month = coldest_month = {}
        
        return {
            "extreme_analysis": (
                f"The highest temperature recorded was {record_high:.1f}°C, while the lowest was "
                f"{record_low:.1f}°C, showing a remarkable temperature range of {abs(record_high - record_low):.1f}°C "
                f"across Australia's diverse climate zones."
            ),
            "seasonal_temperature": (
                f"{hottest_name} emerges as the hottest month with average maximum temperatures of "
                f"{hottest_month.get('avg_max_temp', 0) or 0:.1f}°C, while {coldest_name} is the coldest "
                f"with average minimums of {coldest_month.get('avg_min_temp', 0) or 0:.1f}°C."
            ),
            "temperature_classification": self._classify_temperature_extremes(record_high, record_low)
        }

    def _analyze_rainfall(self, stats: Dict) -> Dict[str, str]:
        """Analyze rainfall patterns with detailed insights"""
        overall = stats.get('overall', {})
        rainfall_dist = stats.get('rainfall_distribution', {})
        
        avg_rain = overall.get('overall_avg_rain', 0) or 0
        record_rain = overall.get('record_rainfall', 0) or 0
        total_records = rainfall_dist.get('total_rain_records', 1) or 1
        
        no_rain_pct = (rainfall_dist.get('no_rain_days', 0) or 0) / total_records * 100
        rain_days_pct = 100 - no_rain_pct
        
        return {
            "rainfall_overview": (
                f"Rainfall analysis shows {rain_days_pct:.1f}% of days experience measurable precipitation, "
                f"with an average daily rainfall of {avg_rain:.1f}mm. The highest single-day rainfall "
                f"recorded was {record_rain:.1f}mm, indicating significant weather variability."
            ),
            "rainfall_distribution": self._describe_rainfall_distribution(rainfall_dist),
            "drought_flood_analysis": self._analyze_drought_flood_patterns(rainfall_dist, avg_rain)
        }

    def _analyze_seasonal_patterns(self, stats: Dict) -> Dict[str, str]:
        """Identify and describe seasonal weather patterns"""
        monthly = stats.get('monthly', []) or []
        
        if not monthly:
            return {"pattern": "Insufficient data for seasonal analysis"}
        
        # Analyze seasonal variations
        seasonal_analysis = self._calculate_seasonal_metrics(monthly)
        
        return {
            "temperature_seasonality": (
                f"Temperature shows strong seasonal variation with {seasonal_analysis.get('temp_range', 0):.1f}°C "
                f"difference between hottest and coldest months. The temperature curve follows typical "
                f"southern hemisphere patterns with peaks in {seasonal_analysis.get('peak_season', 'summer')}."
            ),
            "rainfall_seasonality": (
                f"Rainfall patterns indicate {seasonal_analysis.get('rain_pattern', 'variable')} characteristics with "
                f"{seasonal_analysis.get('wettest_season', 'unknown')} being the wettest period and "
                f"{seasonal_analysis.get('driest_season', 'unknown')} the driest."
            )
        }

    def _analyze_extremes(self, stats: Dict) -> Dict[str, str]:
        """Analyze extreme weather events and their frequency"""
        overall = stats.get('overall', {})
        
        record_high = overall.get('record_high', 0) or 0
        record_low = overall.get('record_low', 0) or 0
        record_rain = overall.get('record_rainfall', 0) or 0
        
        extreme_analysis = {
            "heat_analysis": self._classify_heat_extremes(record_high),
            "cold_analysis": self._classify_cold_extremes(record_low),
            "precipitation_extremes": self._classify_rain_extremes(record_rain),
            "climate_resilience": self._assess_climate_resilience(record_high, record_low, record_rain)
        }
        
        return extreme_analysis

    def _analyze_stations(self, stats: Dict) -> Dict[str, str]:
        """Analyze weather station coverage and data quality"""
        overall = stats.get('overall', {})
        
        total_stations = overall.get('total_stations', 0) or 0
        total_records = overall.get('total_records', 0) or 0
        
        avg_records_per_station = total_records / max(total_stations, 1)
        
        return {
            "coverage_analysis": (
                f"Data from {total_stations} weather stations provides comprehensive coverage across "
                f"Australia, with an average of {avg_records_per_station:.0f} records per station. "
                f"This extensive network ensures reliable regional weather pattern analysis."
            ),
            "data_quality": self._assess_data_quality(total_records, total_stations)
        }

    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """Generate actionable insights based on weather patterns"""
        overall = stats.get('overall', {})
        
        avg_max = overall.get('overall_avg_max', 25) or 25
        avg_min = overall.get('overall_avg_min', 15) or 15
        avg_rain = overall.get('overall_avg_rain', 0) or 0
        
        recommendations = []
        
        # Temperature-based recommendations
        if avg_max > 30:
            recommendations.append("High average temperatures suggest heat stress mitigation strategies are essential")
        elif avg_max < 20:
            recommendations.append("Cool temperatures indicate energy planning for heating requirements")
            
        # Rainfall-based recommendations
        if avg_rain < 1:
            recommendations.append("Low rainfall patterns suggest water conservation and drought preparedness measures")
        elif avg_rain > 5:
            recommendations.append("High rainfall indicates need for flood management and water infrastructure")
            
        # Seasonal recommendations
        temp_range = abs(avg_max - avg_min)
        if temp_range > 15:
            recommendations.append("Large diurnal temperature variation requires adaptive infrastructure design")
            
        recommendations.append("Regular monitoring of extreme weather events recommended for climate adaptation")
        
        return recommendations

    # Helper methods for classification and analysis
    def _classify_climate(self, avg_max: float, avg_min: float) -> str:
        """Classify climate type based on temperature averages"""
        if avg_max > 35:
            return "hot arid"
        elif avg_max > 25 and avg_min > 15:
            return "temperate warm"
        elif avg_max > 20 and avg_min > 10:
            return "temperate mild"
        elif avg_max < 15:
            return "cool temperate"
        else:
            return "moderate temperate"

    def _classify_temperature_extremes(self, high: float, low: float) -> str:
        """Classify temperature extremes for context"""
        if high > 45:
            heat_level = "extreme"
        elif high > 40:
            heat_level = "severe"
        else:
            heat_level = "moderate"
            
        if low < -5:
            cold_level = "extreme"
        elif low < 0:
            cold_level = "severe"
        else:
            cold_level = "mild"
            
        return f"Temperature extremes show {heat_level} heat events and {cold_level} cold conditions"

    def _fallback_insights(self) -> Dict[str, Any]:
        """Fallback insights when data unavailable (graceful degradation)"""
        return {
            "overview": "Weather data analysis temporarily unavailable. System operating in offline mode with cached insights from Australia's diverse climate patterns showing typical seasonal variations and regional differences.",
            "temperature_analysis": {
                "extreme_analysis": "Australia experiences significant temperature variations across its continental climate zones",
                "seasonal_temperature": "Seasonal patterns follow southern hemisphere cycles with summer peaks and winter minimums",
                "temperature_classification": "Temperature ranges typical of Australian continental and coastal climate zones"
            },
            "rainfall_analysis": {
                "rainfall_overview": "Australian rainfall patterns show high variability with seasonal and regional differences",
                "rainfall_distribution": "Precipitation varies from arid inland regions to tropical northern areas",
                "drought_flood_analysis": "Climate variability includes both drought and flood risk patterns"
            },
            "seasonal_patterns": {
                "temperature_seasonality": "Clear seasonal temperature cycles with summer maximums and winter minimums",
                "rainfall_seasonality": "Seasonal rainfall patterns vary by region with monsoon and Mediterranean influences"
            },
            "recommendations": [
                "Monitor extreme weather events for climate adaptation planning",
                "Consider regional climate variations in infrastructure design",
                "Implement water management strategies for variable rainfall patterns"
            ],
            "_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "analysis_method": "fallback",
                "status": "offline_mode"
            }
        }

    def _describe_rainfall_distribution(self, rainfall_dist: Dict) -> str:
        """Describe rainfall distribution patterns"""
        total = rainfall_dist.get('total_rain_records', 1) or 1
        light_pct = (rainfall_dist.get('light_rain_days', 0) or 0) / total * 100
        heavy_pct = (rainfall_dist.get('heavy_rain_days', 0) or 0) / total * 100
        
        return (
            f"Precipitation distribution shows {light_pct:.1f}% light rainfall events and "
            f"{heavy_pct:.1f}% heavy rainfall days, indicating varied weather intensity patterns."
        )

    def _calculate_seasonal_metrics(self, monthly: List[Dict]) -> Dict:
        """Calculate seasonal metrics from monthly data"""
        if not monthly:
            return {}
            
        temps = [m.get('avg_max_temp', 0) or 0 for m in monthly]
        rains = [m.get('avg_rainfall', 0) or 0 for m in monthly]
        
        if not temps or not rains:
            return {}
        
        hottest_idx = temps.index(max(temps))
        coldest_idx = temps.index(min(temps))
        wettest_idx = rains.index(max(rains))
        driest_idx = rains.index(min(rains))
        
        return {
            'temp_range': max(temps) - min(temps),
            'peak_season': calendar.month_name[hottest_idx + 1],
            'wettest_season': calendar.month_name[wettest_idx + 1],
            'driest_season': calendar.month_name[driest_idx + 1],
            'rain_pattern': 'seasonal' if max(rains) > 2 * min(rains) else 'uniform'
        }

    def _assess_data_quality(self, total_records: int, total_stations: int) -> str:
        """Assess data quality based on coverage metrics"""
        if total_records > 100000:
            quality = "excellent"
        elif total_records > 50000:
            quality = "good"
        elif total_records > 10000:
            quality = "adequate"
        else:
            quality = "limited"
            
        return f"Data quality assessment: {quality} ({total_records:,} records from {total_stations} stations)"

    def _classify_heat_extremes(self, temp: float) -> str:
        if temp > 50:
            return "Exceptional heat events exceeding 50°C pose significant health and infrastructure risks"
        elif temp > 45:
            return "Extreme heat events above 45°C require emergency preparedness protocols"
        else:
            return "Moderate heat extremes within typical Australian temperature ranges"

    def _classify_cold_extremes(self, temp: float) -> str:
        if temp < -10:
            return "Severe cold events below -10°C indicate continental climate influences"
        elif temp < 0:
            return "Frost conditions below 0°C affect agriculture and water systems"
        else:
            return "Mild cold temperatures within temperate range expectations"

    def _classify_rain_extremes(self, rain: float) -> str:
        if rain > 200:
            return "Extreme precipitation events exceeding 200mm indicate significant flood potential"
        elif rain > 100:
            return "Heavy rainfall events above 100mm require flood management considerations"
        else:
            return "Moderate precipitation extremes within regional climate patterns"

    def _assess_climate_resilience(self, high: float, low: float, rain: float) -> str:
        """Assess overall climate resilience needs"""
        extremes_count = sum([
            1 if high > 40 else 0,
            1 if low < 5 else 0,
            1 if rain > 100 else 0
        ])
        
        if extremes_count >= 2:
            return "Multiple extreme weather indicators suggest comprehensive climate adaptation strategies needed"
        elif extremes_count == 1:
            return "Moderate climate variability requires targeted adaptation measures"
        else:
            return "Stable climate conditions with standard resilience measures appropriate"

    def _analyze_drought_flood_patterns(self, rainfall_dist: Dict, avg_rain: float) -> str:
        """Analyze drought and flood risk patterns"""
        total = rainfall_dist.get('total_rain_records', 1) or 1
        no_rain_pct = (rainfall_dist.get('no_rain_days', 0) or 0) / total * 100
        extreme_rain_pct = (rainfall_dist.get('extreme_rain_days', 0) or 0) / total * 100
        
        if no_rain_pct > 60:
            drought_risk = "high"
        elif no_rain_pct > 40:
            drought_risk = "moderate"
        else:
            drought_risk = "low"
            
        if extreme_rain_pct > 5:
            flood_risk = "significant"
        elif extreme_rain_pct > 2:
            flood_risk = "moderate"
        else:
            flood_risk = "low"
            
        return (
            f"Climate risk analysis indicates {drought_risk} drought risk ({no_rain_pct:.1f}% dry days) "
            f"and {flood_risk} flood risk ({extreme_rain_pct:.1f}% extreme rainfall events)"
        )

    def _analyze_trends(self, stats: Dict) -> Dict[str, str]:
        """Analyze temporal trends in the weather data"""
        monthly = stats.get('monthly', []) or []
        
        if len(monthly) < 12:
            return {"trend_analysis": "Insufficient temporal data for trend analysis"}
        
        # Simple trend analysis based on monthly variations
        temp_variation = max([m.get('avg_max_temp', 0) or 0 for m in monthly]) - min([m.get('avg_max_temp', 0) or 0 for m in monthly])
        rain_variation = max([m.get('avg_rainfall', 0) or 0 for m in monthly]) - min([m.get('avg_rainfall', 0) or 0 for m in monthly])
        
        return {
            "temperature_trends": (
                f"Temperature shows {temp_variation:.1f}°C seasonal variation, indicating "
                f"{'strong' if temp_variation > 20 else 'moderate' if temp_variation > 10 else 'weak'} "
                f"seasonal temperature cycling patterns"
            ),
            "precipitation_trends": (
                f"Rainfall variation of {rain_variation:.1f}mm suggests "
                f"{'highly seasonal' if rain_variation > 50 else 'moderately seasonal' if rain_variation > 20 else 'uniform'} "
                f"precipitation distribution throughout the year"
            )
        }