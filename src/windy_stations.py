"""
Windy Stations API Fetcher
Fetches real-time weather station data near the location
"""
import requests
from typing import Dict, Any, Optional


def fetch_station_data(api_key: str, lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch real-time data from nearby Windy weather stations
    
    Note: This requires a Windy Stations API key from stations.windy.com
    If no API key is provided or stations not available, returns empty data
    
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
    
    # Try different API endpoints
    try:
        # Method 1: Get nearby stations using lat/lon
        nearby_url = f"https://stations.windy.com/pws/stations/nearby"
        params = {
            "lat": lat,
            "lon": lon,
            "limit": 5,
            "key": api_key
        }
        response = requests.get(nearby_url, params=params, timeout=15)
        
        if response.status_code == 200:
            stations = response.json()
            if stations:
                nearest = stations[0]  # First is nearest
                return fetch_single_station(api_key, nearest)
        
        # Method 2: Get open data stations and find nearest
        open_url = f"https://stations.windy.com/pws/stations/open"
        params = {"key": api_key}
        response = requests.get(open_url, params=params, timeout=15)
        
        if response.status_code == 200:
            stations = response.json()
            nearest = find_nearest_station(stations, lat, lon)
            if nearest:
                return fetch_single_station(api_key, nearest)
        
        # Method 3: Try legacy endpoint format
        legacy_url = f"https://stations.windy.com/pws/stations/open/{api_key}"
        response = requests.get(legacy_url, timeout=15)
        
        if response.status_code == 200:
            stations = response.json()
            nearest = find_nearest_station(stations, lat, lon)
            if nearest:
                station_id = nearest.get("id")
                data_url = f"https://stations.windy.com/pws/station/open/{api_key}/{station_id}"
                data_response = requests.get(data_url, timeout=15)
                if data_response.status_code == 200:
                    return process_station_data(data_response.json(), nearest)
        
        return {
            "available": False,
            "message": f"No stations found in Bodrum area (API returned {response.status_code})"
        }
        
    except requests.RequestException as e:
        return {
            "available": False,
            "message": f"API error: {str(e)}"
        }


def fetch_single_station(api_key: str, station: Dict) -> Dict[str, Any]:
    """Fetch data from a single station"""
    station_id = station.get("id") or station.get("stationId")
    
    if not station_id:
        return {"available": False, "message": "No station ID found"}
    
    try:
        # Try different data endpoints
        endpoints = [
            f"https://stations.windy.com/pws/station/open/{api_key}/{station_id}",
            f"https://stations.windy.com/pws/station/{station_id}?key={api_key}"
        ]
        
        for url in endpoints:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return process_station_data(data, {
                    "id": station_id,
                    "name": station.get("name", "Unknown"),
                    "distance_km": station.get("distance_km", station.get("distance", 0))
                })
        
        return {"available": False, "message": f"Could not fetch station {station_id}"}
        
    except requests.RequestException as e:
        return {"available": False, "message": f"Station fetch error: {str(e)}"}


def find_nearest_station(stations: list, lat: float, lon: float, max_distance_km: float = 50) -> Optional[Dict]:
    """Find the nearest station within max_distance_km"""
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return 2 * 6371 * asin(sqrt(a))  # km
    
    nearest = None
    min_distance = float('inf')
    
    for station in stations:
        try:
            s_lat = station.get("lat") or station.get("latitude")
            s_lon = station.get("lon") or station.get("longitude")
            
            if s_lat is None or s_lon is None:
                continue
            
            distance = haversine(lat, lon, float(s_lat), float(s_lon))
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest = {
                    "id": station.get("id") or station.get("stationId"),
                    "name": station.get("name", "Unknown"),
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
    
    # Handle both list and dict responses
    latest = data[-1] if isinstance(data, list) and data else data
    
    result = {
        "available": True,
        "station_name": station_info.get("name", "Unknown"),
        "distance_km": station_info.get("distance_km", 0),
        "timestamp": latest.get("ts") or latest.get("timestamp"),
        "measurements": {}
    }
    
    # Extract available measurements
    if "temp" in latest:
        result["measurements"]["temperature_c"] = latest["temp"]
    
    if "wind" in latest:
        wind_ms = latest["wind"]
        result["measurements"]["wind_knots"] = round(wind_ms * MS_TO_KNOTS, 1)
    
    if "gust" in latest:
        gust_ms = latest["gust"]
        result["measurements"]["gust_knots"] = round(gust_ms * MS_TO_KNOTS, 1)
    
    if "windDir" in latest:
        result["measurements"]["wind_direction"] = latest["windDir"]
    
    if "pressure" in latest:
        result["measurements"]["pressure_hpa"] = latest["pressure"]
    
    if "humidity" in latest or "rh" in latest:
        result["measurements"]["humidity"] = latest.get("humidity") or latest.get("rh")
    
    return result
