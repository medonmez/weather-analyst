"""
Open-Meteo Weather API Fetcher
Fetches weather data from multiple models for comparison
"""
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional


def fetch_weather_data(lat: float, lon: float, models: List[str], target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch weather forecast from multiple models
    
    Args:
        lat: Latitude
        lon: Longitude
        models: List of model names
        target_date: Target date in YYYY-MM-DD format (default: today)
    
    Returns:
        Dictionary with model forecasts
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    base_url = "https://api.open-meteo.com/v1/forecast"
    
    # Essential parameters only
    hourly_params = [
        "temperature_2m",
        "precipitation_probability",
        "precipitation",
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
            "forecast_days": 3,
            "wind_speed_unit": "kn"
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results[model] = process_weather_data(data, target_date)
            
        except requests.RequestException as e:
            results[model] = {"error": str(e)}
    
    return results


def process_weather_data(data: Dict, target_date: str) -> Dict[str, Any]:
    """Process raw API response into structured format"""
    if "hourly" not in data:
        return {"error": "No hourly data"}
    
    hourly = data["hourly"]
    times = hourly.get("time", [])
    
    # Find target date's daytime hours (08:00 - 18:00)
    daytime_indices = []
    for i, time_str in enumerate(times):
        if target_date in time_str:
            hour = int(time_str.split("T")[1].split(":")[0])
            if 8 <= hour <= 18:
                daytime_indices.append(i)
    
    if not daytime_indices:
        return {"error": f"No data for {target_date}"}
    
    # Extract values for daytime, filtering out None values
    def get_values(key):
        values = hourly.get(key, [])
        return [values[i] for i in daytime_indices if i < len(values) and values[i] is not None]
    
    # Wind is already in knots (requested via API param)
    wind_speeds = get_values("wind_speed_10m")
    wind_gusts = get_values("wind_gusts_10m")
    temps = get_values("temperature_2m")
    precip_probs = get_values("precipitation_probability")
    
    return {
        "target_date": target_date,
        "times": [times[i] for i in daytime_indices if i < len(times)],
        "temperature_c": temps,
        "precipitation_probability_pct": precip_probs,
        "precipitation_mm": get_values("precipitation"),
        "visibility_m": get_values("visibility"),
        "wind_speed_knots": wind_speeds,
        "wind_direction_deg": get_values("wind_direction_10m"),
        "wind_gusts_knots": wind_gusts,
        "summary": {
            "avg_wind_knots": round(sum(wind_speeds) / len(wind_speeds), 1) if wind_speeds else 0,
            "max_wind_knots": round(max(wind_speeds), 1) if wind_speeds else 0,
            "max_gust_knots": round(max(wind_gusts), 1) if wind_gusts else 0,
            "avg_temp_c": round(sum(temps) / len(temps), 1) if temps else 0,
            "max_precip_prob_pct": max(precip_probs) if precip_probs else 0
        }
    }


def get_model_display_name(model_id: str) -> str:
    """Get human-readable model name"""
    names = {
        "ecmwf_ifs": "ECMWF IFS",
        "ecmwf_ifs025": "ECMWF IFS 0.25",
        "ecmwf_ifs04": "ECMWF IFS HRES 9km",
        "ecmwf_aifs025": "ECMWF AIFS",
        "ecmwf_aifs025_single": "ECMWF AIFS Single",
        "icon_seamless": "ICON (DWD)",
        "icon_eu": "ICON-EU (DWD)",
        "gfs_seamless": "GFS (NOAA)",
        "meteofrance_seamless": "Meteo-France",
        "arpege_seamless": "ARPEGE",
        "gem_seamless": "GEM (Canada)"
    }
    return names.get(model_id, model_id)
