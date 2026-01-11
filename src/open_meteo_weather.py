"""
Open-Meteo Weather API Fetcher
Fetches weather data from multiple models for comparison
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Conversion factor: m/s to knots
MS_TO_KNOTS = 1.94384


def fetch_weather_data(lat: float, lon: float, models: List[str]) -> Dict[str, Any]:
    """
    Fetch weather forecast from multiple models
    
    Args:
        lat: Latitude
        lon: Longitude
        models: List of model names (e.g., ["icon_seamless", "gfs_seamless"])
    
    Returns:
        Dictionary with model forecasts
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    
    # Parameters to fetch
    hourly_params = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_probability",
        "precipitation",
        "weather_code",
        "visibility",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m"
    ]
    
    results = {}
    
    for model in models:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(hourly_params),
            "models": model,
            "timezone": "Europe/Istanbul",
            "forecast_days": 2
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Process and structure the data
            results[model] = process_weather_data(data)
            
        except requests.RequestException as e:
            results[model] = {"error": str(e)}
    
    return results


def process_weather_data(data: Dict) -> Dict[str, Any]:
    """Process raw API response into structured format"""
    if "hourly" not in data:
        return {"error": "No hourly data"}
    
    hourly = data["hourly"]
    times = hourly.get("time", [])
    
    # Find today's daytime hours (08:00 - 18:00)
    today = datetime.now().strftime("%Y-%m-%d")
    
    daytime_indices = []
    for i, time_str in enumerate(times):
        if today in time_str:
            hour = int(time_str.split("T")[1].split(":")[0])
            if 8 <= hour <= 18:
                daytime_indices.append(i)
    
    if not daytime_indices:
        # If no today data, use first available daytime hours
        for i, time_str in enumerate(times):
            hour = int(time_str.split("T")[1].split(":")[0])
            if 8 <= hour <= 18:
                daytime_indices.append(i)
                if len(daytime_indices) >= 11:
                    break
    
    # Extract values for daytime
    def get_values(key):
        values = hourly.get(key, [])
        return [values[i] for i in daytime_indices if i < len(values)]
    
    wind_speeds_ms = get_values("wind_speed_10m")
    wind_gusts_ms = get_values("wind_gusts_10m")
    
    # Convert to knots
    wind_speeds_knots = [v * MS_TO_KNOTS if v else 0 for v in wind_speeds_ms]
    wind_gusts_knots = [v * MS_TO_KNOTS if v else 0 for v in wind_gusts_ms]
    
    return {
        "times": [times[i] for i in daytime_indices if i < len(times)],
        "temperature": get_values("temperature_2m"),
        "humidity": get_values("relative_humidity_2m"),
        "precipitation_probability": get_values("precipitation_probability"),
        "precipitation": get_values("precipitation"),
        "weather_code": get_values("weather_code"),
        "visibility": get_values("visibility"),
        "wind_speed_knots": wind_speeds_knots,
        "wind_direction": get_values("wind_direction_10m"),
        "wind_gusts_knots": wind_gusts_knots,
        # Summary stats
        "summary": {
            "avg_wind_knots": round(sum(wind_speeds_knots) / len(wind_speeds_knots), 1) if wind_speeds_knots else 0,
            "max_wind_knots": round(max(wind_speeds_knots), 1) if wind_speeds_knots else 0,
            "max_gust_knots": round(max(wind_gusts_knots), 1) if wind_gusts_knots else 0,
            "avg_temp": round(sum(get_values("temperature_2m")) / len(get_values("temperature_2m")), 1) if get_values("temperature_2m") else 0,
            "max_precip_prob": max(get_values("precipitation_probability")) if get_values("precipitation_probability") else 0
        }
    }


def get_model_display_name(model_id: str) -> str:
    """Get human-readable model name"""
    names = {
        "icon_seamless": "ICON (DWD)",
        "gfs_seamless": "GFS (NOAA)",
        "ecmwf_ifs025": "ECMWF IFS",
        "arpege_seamless": "ARPEGE (Météo-France)",
        "gem_seamless": "GEM (Canada)"
    }
    return names.get(model_id, model_id)
