"""
Station Data Fetcher
Fetches real-time weather data from WMO/METAR stations
Uses Aviation Weather Center API (NOAA) - free, no API key needed
"""
import requests
from typing import Dict, Any
from datetime import datetime


# Bodrum - WMO 17290, ICAO: LTFE
DEFAULT_STATION = {
    "icao": "LTFE",
    "wmo": "17290"
}


def fetch_station_data(api_key: str = None, lat: float = None, lon: float = None, 
                       icao: str = None) -> Dict[str, Any]:
    """
    Fetch real-time METAR data from aviation weather stations
    
    Uses Aviation Weather Center API (NOAA) - free, no API key required
    
    Args:
        api_key: Not used (kept for compatibility)
        lat, lon: Not used (we use specific ICAO code)
        icao: ICAO airport code (default: LTFE for Bodrum)
    
    Returns:
        Dictionary with station measurements
    """
    station_icao = icao or DEFAULT_STATION["icao"]
    
    try:
        # Aviation Weather Center API - free, no key needed
        url = f"https://aviationweather.gov/api/data/metar"
        params = {
            "ids": station_icao,
            "format": "json",
            "hours": 1
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return {
                "available": False,
                "message": f"METAR API error: {response.status_code}"
            }
        
        data = response.json()
        
        if not data:
            return {
                "available": False,
                "message": f"No METAR data for {station_icao}"
            }
        
        return process_metar_data(data[0])
        
    except requests.RequestException as e:
        return {
            "available": False,
            "message": f"Network error: {str(e)}"
        }
    except (KeyError, IndexError, ValueError) as e:
        return {
            "available": False,
            "message": f"Data parsing error: {str(e)}"
        }


def process_metar_data(metar: Dict) -> Dict[str, Any]:
    """Process METAR JSON into standardized format"""
    
    MS_TO_KNOTS = 1.94384
    
    result = {
        "available": True,
        "station_icao": metar.get("icaoId", DEFAULT_STATION["icao"]),
        "station_wmo": DEFAULT_STATION["wmo"],
        "observation_time": metar.get("reportTime"),
        "raw_metar": metar.get("rawOb"),
        "measurements": {}
    }
    
    # Temperature (Celsius)
    if "temp" in metar and metar["temp"] is not None:
        result["measurements"]["temperature_c"] = round(metar["temp"], 1)
    
    # Dew point
    if "dewp" in metar and metar["dewp"] is not None:
        result["measurements"]["dewpoint_c"] = round(metar["dewp"], 1)
    
    # Wind speed (METAR gives in knots)
    if "wspd" in metar and metar["wspd"] is not None:
        result["measurements"]["wind_knots"] = metar["wspd"]
    
    # Wind gusts
    if "wgst" in metar and metar["wgst"] is not None:
        result["measurements"]["gust_knots"] = metar["wgst"]
    
    # Wind direction
    if "wdir" in metar and metar["wdir"] is not None:
        if isinstance(metar["wdir"], (int, float)):
            result["measurements"]["wind_direction"] = metar["wdir"]
        elif metar["wdir"] == "VRB":
            result["measurements"]["wind_direction"] = "Değişken"
    
    # Visibility (meters)
    if "visib" in metar and metar["visib"] is not None:
        try:
            # METAR visibility is in statute miles, convert to km
            vis_value = metar["visib"]
            if isinstance(vis_value, str):
                # Handle values like "6+" or "P6" (greater than 6)
                vis_value = vis_value.replace("+", "").replace("P", "")
                vis_value = float(vis_value)
            vis_km = float(vis_value) * 1.60934
            result["measurements"]["visibility_km"] = round(vis_km, 1)
        except (ValueError, TypeError):
            pass  # Skip if can't parse
    
    # Pressure (altimeter - API returns in hPa)
    if "altim" in metar and metar["altim"] is not None:
        result["measurements"]["pressure_hpa"] = round(metar["altim"], 1)
    
    # Cloud cover
    if "clouds" in metar and metar["clouds"]:
        clouds = metar["clouds"]
        if isinstance(clouds, list) and clouds:
            result["measurements"]["clouds"] = [
                {"cover": c.get("cover"), "base_ft": c.get("base")} 
                for c in clouds if isinstance(c, dict)
            ]
    
    # Weather phenomena
    if "wxString" in metar and metar["wxString"]:
        result["measurements"]["weather"] = metar["wxString"]
    
    # Flight category (VFR, MVFR, IFR, LIFR)
    if "fltcat" in metar:
        result["measurements"]["flight_category"] = metar["fltcat"]
    
    return result
