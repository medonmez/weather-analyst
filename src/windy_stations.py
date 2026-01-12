"""
Windy Stations API Fetcher
Fetches real-time weather station data near the location
"""
import requests
from typing import Dict, Any, Optional
from math import radians, cos, sin, asin, sqrt


def fetch_station_data(api_key: str, lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch real-time data from nearby Windy weather stations
    
    Args:
        api_key: Windy Stations API key
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dictionary with station data or empty if unavailable
    """
    if not api_key:
        return {
            "available": False,
            "message": "Windy API key not configured"
        }
    
    try:
        # Get open data stations
        open_url = f"https://stations.windy.com/pws/stations/open/{api_key}"
        response = requests.get(open_url, timeout=15)
        
        if response.status_code != 200:
            return {
                "available": False,
                "message": f"Windy API error: {response.status_code}"
            }
        
        stations = response.json()
        
        if not stations:
            return {
                "available": False,
                "message": "No open data stations available"
            }
        
        # Find nearest station to Bodrum
        nearest = find_nearest_station(stations, lat, lon, max_distance_km=100)
        
        if not nearest:
            return {
                "available": False,
                "message": f"No stations within 100km of location (checked {len(stations)} stations)"
            }
        
        # Fetch station data
        station_id = nearest["id"]
        data_url = f"https://stations.windy.com/pws/station/open/{api_key}/{station_id}"
        data_response = requests.get(data_url, timeout=15)
        
        if data_response.status_code != 200:
            return {
                "available": False,
                "message": f"Could not fetch station data: {data_response.status_code}"
            }
        
        return process_station_data(data_response.json(), nearest)
        
    except requests.RequestException as e:
        return {
            "available": False,
            "message": f"API error: {str(e)}"
        }


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in km"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * 6371 * asin(sqrt(a))


def find_nearest_station(stations: list, lat: float, lon: float, max_distance_km: float = 100) -> Optional[Dict]:
    """Find the nearest station within max_distance_km"""
    nearest = None
    min_distance = float('inf')
    
    for station in stations:
        try:
            # Try different field names for coordinates
            s_lat = station.get("lat") or station.get("latitude")
            s_lon = station.get("lon") or station.get("longitude")
            
            if s_lat is None or s_lon is None:
                continue
            
            s_lat = float(s_lat)
            s_lon = float(s_lon)
            
            distance = haversine(lat, lon, s_lat, s_lon)
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest = {
                    "id": station.get("id") or station.get("stationId"),
                    "name": station.get("name", "Unknown Station"),
                    "distance_km": round(distance, 1),
                    "lat": s_lat,
                    "lon": s_lon
                }
        except (TypeError, ValueError):
            continue
    
    return nearest


def process_station_data(data: Dict, station_info: Dict) -> Dict[str, Any]:
    """Process station data into standardized format"""
    MS_TO_KNOTS = 1.94384
    
    # Handle list response (multiple readings)
    if isinstance(data, list) and data:
        latest = data[-1]
    elif isinstance(data, dict):
        latest = data
    else:
        return {
            "available": False,
            "message": "Invalid station data format"
        }
    
    result = {
        "available": True,
        "station_name": station_info.get("name", "Unknown"),
        "distance_km": station_info.get("distance_km", 0),
        "lat": station_info.get("lat"),
        "lon": station_info.get("lon"),
        "timestamp": latest.get("ts") or latest.get("timestamp"),
        "measurements": {}
    }
    
    # Extract available measurements
    if "temp" in latest and latest["temp"] is not None:
        result["measurements"]["temperature_c"] = round(latest["temp"], 1)
    
    if "wind" in latest and latest["wind"] is not None:
        wind_ms = latest["wind"]
        result["measurements"]["wind_knots"] = round(wind_ms * MS_TO_KNOTS, 1)
        result["measurements"]["wind_ms"] = round(wind_ms, 1)
    
    if "gust" in latest and latest["gust"] is not None:
        gust_ms = latest["gust"]
        result["measurements"]["gust_knots"] = round(gust_ms * MS_TO_KNOTS, 1)
    
    if "windDir" in latest and latest["windDir"] is not None:
        result["measurements"]["wind_direction"] = latest["windDir"]
    
    if "pressure" in latest and latest["pressure"] is not None:
        result["measurements"]["pressure_hpa"] = latest["pressure"]
    
    if ("humidity" in latest and latest["humidity"] is not None) or ("rh" in latest and latest["rh"] is not None):
        result["measurements"]["humidity"] = latest.get("humidity") or latest.get("rh")
    
    # If no measurements found, mark as unavailable
    if not result["measurements"]:
        return {
            "available": False,
            "message": f"Station {station_info.get('name')} has no current data"
        }
    
    return result
