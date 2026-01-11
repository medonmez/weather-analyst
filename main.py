#!/usr/bin/env python3
"""
Weather Analyst - Main Orchestrator
Dalis Kulubu icin hava durumu analiz sistemi
"""
import sys
import argparse
from datetime import datetime, timedelta, timezone

from config import (
    LOCATION, WEATHER_MODELS, 
    OPENROUTER_API_KEY, RESEND_API_KEY, WINDY_API_KEY,
    EMAIL_TO, EMAIL_FROM,
    LLM_MODEL, SYSTEM_PROMPT
)
from src.open_meteo_weather import fetch_weather_data
from src.open_meteo_marine import fetch_marine_data
from src.windy_stations import fetch_station_data
from src.llm_analyzer import analyze_weather
from src.email_service import send_report_email
from src.visualizer import create_windguru_chart

# Turkey timezone (UTC+3)
TURKEY_TZ = timezone(timedelta(hours=3))


def get_turkey_now():
    """Get current time in Turkey timezone"""
    return datetime.now(TURKEY_TZ)


def main(test_mode: bool = False, no_email: bool = False, forecast_day: str = "today"):
    """
    Main orchestration function
    
    Args:
        test_mode: If True, print output instead of sending email
        no_email: If True, skip email sending
        forecast_day: "today" or "tomorrow"
    """
    # Use Turkey time for date calculations
    now_tr = get_turkey_now()
    
    # Determine target date
    if forecast_day == "tomorrow":
        target_date = (now_tr + timedelta(days=1)).strftime("%Y-%m-%d")
        report_title = "Yarin"
    else:
        target_date = now_tr.strftime("%Y-%m-%d")
        report_title = "Bugun"
    
    print(f"Weather Analyst - {now_tr.strftime('%Y-%m-%d %H:%M')} (TR)")
    print(f"Location: {LOCATION['name']}")
    print(f"Forecast for: {target_date} ({report_title})")
    print("-" * 50)
    
    # 1. Fetch weather data from multiple models
    print("Fetching weather forecasts...")
    weather_data = fetch_weather_data(
        lat=LOCATION["lat"],
        lon=LOCATION["lon"],
        models=WEATHER_MODELS,
        target_date=target_date
    )
    
    for model, data in weather_data.items():
        if "error" in data:
            print(f"  [ERROR] {model}: {data['error']}")
        else:
            summary = data.get("summary", {})
            print(f"  [OK] {model}: {summary.get('avg_wind_knots', '?')} knot avg, max {summary.get('max_wind_knots', '?')} knot")
    
    # 2. Fetch marine data
    print("\nFetching marine data...")
    marine_data = fetch_marine_data(
        lat=LOCATION["lat"],
        lon=LOCATION["lon"],
        target_date=target_date
    )
    
    if "error" in marine_data:
        print(f"  [ERROR] Marine: {marine_data['error']}")
    else:
        summary = marine_data.get("summary", {})
        print(f"  [OK] Waves: {summary.get('avg_wave_height_m', '?')}m avg, {summary.get('max_wave_height_m', '?')}m max")
    
    # 3. Fetch real-time station data (only for today)
    print("\nFetching station data...")
    if forecast_day == "today":
        station_data = fetch_station_data(
            api_key=WINDY_API_KEY,
            lat=LOCATION["lat"],
            lon=LOCATION["lon"]
        )
        if station_data.get("available"):
            print(f"  [OK] Station: {station_data.get('station_name')}")
        else:
            print(f"  [INFO] {station_data.get('message', 'No station data')}")
    else:
        station_data = {"available": False, "message": "Station data not applicable for tomorrow forecast"}
        print("  [INFO] Station data skipped for tomorrow forecast")
    
    # 4. Generate Windguru-style chart
    print("\nGenerating chart...")
    chart_bytes = create_windguru_chart(weather_data, marine_data, target_date)
    if chart_bytes:
        print("  [OK] Chart generated")
    else:
        print("  [INFO] Chart generation skipped (matplotlib not available)")
    
    # 5. Analyze with LLM
    print("\nAnalyzing with LLM...")
    analysis = analyze_weather(
        weather_data=weather_data,
        marine_data=marine_data,
        station_data=station_data,
        api_key=OPENROUTER_API_KEY,
        model=LLM_MODEL,
        system_prompt=SYSTEM_PROMPT,
        location_name=LOCATION["name"],
        forecast_day=forecast_day,
        target_date=target_date
    )
    
    if analysis.startswith("HATA"):
        print(f"  {analysis}")
    else:
        print("  [OK] Analysis complete")
    
    # Prepare raw data for JSON attachment
    raw_data = {
        "generated_at": datetime.now().isoformat(),
        "forecast_for": target_date,
        "forecast_day": forecast_day,
        "location": LOCATION,
        "weather_models": weather_data,
        "marine_data": marine_data,
        "station_data": station_data
    }
    
    # 6. Send email or print
    if test_mode or no_email:
        print("\n" + "=" * 50)
        print("REPORT PREVIEW:")
        print("=" * 50)
        print(analysis)
        print("=" * 50)
        
        if chart_bytes:
            # Save chart locally for testing
            chart_path = f"/tmp/weather_chart_{target_date}.png"
            with open(chart_path, 'wb') as f:
                f.write(chart_bytes)
            print(f"\nChart saved to: {chart_path}")
        
        if no_email:
            print("\nEmail sending skipped (--no-email)")
        else:
            print("\nTest mode - email not sent")
    else:
        print("\nSending email...")
        result = send_report_email(
            api_key=RESEND_API_KEY,
            to_email=EMAIL_TO,
            from_email=EMAIL_FROM,
            location_name=LOCATION["name"],
            analysis=analysis,
            raw_data=raw_data,
            chart_bytes=chart_bytes,
            forecast_day=forecast_day
        )
        
        if result.get("success"):
            print(f"  [OK] Email sent! ID: {result.get('id')}")
        else:
            print(f"  [ERROR] Email failed: {result.get('error')}")
            sys.exit(1)
    
    print("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather Analyst for Diving Club")
    parser.add_argument("--test", action="store_true", help="Test mode - print analysis without sending email")
    parser.add_argument("--no-email", action="store_true", help="Skip email sending")
    parser.add_argument("--day", choices=["today", "tomorrow"], default="today", help="Forecast day")
    
    args = parser.parse_args()
    main(test_mode=args.test, no_email=args.no_email, forecast_day=args.day)
