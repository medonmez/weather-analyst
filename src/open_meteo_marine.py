"""
Open-Meteo Marine API Fetcher
Fetches wave, swell, and sea state data
"""
import requests
from datetime import datetime
from typing import Dict, Any, Optional


def fetch_marine_data(lat: float, lon: float, target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch marine/wave forecast data
    
    Args:
        lat: Latitude
        lon: Longitude
        target_date: Target date in YYYY-MM-DD format (default: today)
    
    Returns:
        Dictionary with marine forecast
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    base_url = "https://marine-api.open-meteo.com/v1/marine"
    
    hourly_params = [
        "wave_height",
        "wave_direction",
        "wave_period",
        "wind_wave_height",
        "wind_wave_direction",
        "wind_wave_period",
        "swell_wave_height",
        "swell_wave_direction",
        "swell_wave_period"
    ]
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(hourly_params),
        "timezone": "Europe/Istanbul",
        "forecast_days": 3
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return process_marine_data(data, target_date)
        
    except requests.RequestException as e:
        return {"error": str(e)}


def process_marine_data(data: Dict, target_date: str) -> Dict[str, Any]:
    """Process raw marine API response"""
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
        return {"error": f"No marine data for {target_date}"}
    
    def get_values(key):
        values = hourly.get(key, [])
        return [values[i] for i in daytime_indices if i < len(values) and values[i] is not None]
    
    wave_heights = get_values("wave_height")
    swell_heights = get_values("swell_wave_height")
    wind_wave_heights = get_values("wind_wave_height")
    swell_periods = get_values("swell_wave_period")
    swell_directions = get_values("swell_wave_direction")
    
    return {
        "target_date": target_date,
        "times": [times[i] for i in daytime_indices if i < len(times)],
        "wave_height_m": wave_heights,
        "wave_direction_deg": get_values("wave_direction"),
        "wave_period_s": get_values("wave_period"),
        "swell_wave_height_m": swell_heights,
        "swell_wave_direction_deg": swell_directions,
        "swell_wave_period_s": swell_periods,
        "wind_wave_height_m": wind_wave_heights,
        "summary": {
            "avg_wave_height_m": round(sum(wave_heights) / len(wave_heights), 2) if wave_heights else 0,
            "max_wave_height_m": round(max(wave_heights), 2) if wave_heights else 0,
            "avg_swell_height_m": round(sum(swell_heights) / len(swell_heights), 2) if swell_heights else 0,
            "max_swell_height_m": round(max(swell_heights), 2) if swell_heights else 0,
            "avg_swell_period_s": round(sum(swell_periods) / len(swell_periods), 1) if swell_periods else 0,
            "primary_swell_direction": get_direction_name(round(sum(swell_directions) / len(swell_directions))) if swell_directions else "N/A"
        }
    }


def get_direction_name(degrees: float) -> str:
    """Convert degrees to cardinal direction"""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]
