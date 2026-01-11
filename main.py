#!/usr/bin/env python3
"""
Weather Analyst - Main Orchestrator
Dalış Kulübü için hava durumu analiz sistemi
"""
import sys
import argparse
from datetime import datetime

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


def main(test_mode: bool = False, no_email: bool = False):
    """
    Main orchestration function
    
    Args:
        test_mode: If True, print output instead of sending email
        no_email: If True, skip email sending
    """
    print(f"🌊 Weather Analyst - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📍 Location: {LOCATION['name']}")
    print("-" * 50)
    
    # 1. Fetch weather data from multiple models
    print("📊 Fetching weather forecasts...")
    weather_data = fetch_weather_data(
        lat=LOCATION["lat"],
        lon=LOCATION["lon"],
        models=WEATHER_MODELS
    )
    
    for model, data in weather_data.items():
        if "error" in data:
            print(f"  ❌ {model}: {data['error']}")
        else:
            summary = data.get("summary", {})
            print(f"  ✅ {model}: {summary.get('avg_wind_knots', '?')} knot avg")
    
    # 2. Fetch marine data
    print("\n🌊 Fetching marine data...")
    marine_data = fetch_marine_data(
        lat=LOCATION["lat"],
        lon=LOCATION["lon"]
    )
    
    if "error" in marine_data:
        print(f"  ❌ Marine: {marine_data['error']}")
    else:
        summary = marine_data.get("summary", {})
        print(f"  ✅ Waves: {summary.get('avg_wave_height', '?')}m avg, {summary.get('max_wave_height', '?')}m max")
    
    # 3. Fetch real-time station data
    print("\n📡 Fetching station data...")
    station_data = fetch_station_data(
        api_key=WINDY_API_KEY,
        lat=LOCATION["lat"],
        lon=LOCATION["lon"]
    )
    
    if station_data.get("available"):
        print(f"  ✅ Station: {station_data.get('station_name')}")
    else:
        print(f"  ℹ️  {station_data.get('message', 'No station data')}")
    
    # 4. Analyze with LLM
    print("\n🤖 Analyzing with LLM...")
    analysis = analyze_weather(
        weather_data=weather_data,
        marine_data=marine_data,
        station_data=station_data,
        api_key=OPENROUTER_API_KEY,
        model=LLM_MODEL,
        system_prompt=SYSTEM_PROMPT,
        location_name=LOCATION["name"]
    )
    
    if analysis.startswith("❌"):
        print(f"  {analysis}")
    else:
        print("  ✅ Analysis complete")
    
    # 5. Send email or print
    if test_mode or no_email:
        print("\n" + "=" * 50)
        print("📧 REPORT PREVIEW:")
        print("=" * 50)
        print(analysis)
        print("=" * 50)
        
        if no_email:
            print("\n⏭️  Email sending skipped (--no-email)")
        else:
            print("\n⏭️  Test mode - email not sent")
    else:
        print("\n📧 Sending email...")
        result = send_report_email(
            api_key=RESEND_API_KEY,
            to_email=EMAIL_TO,
            from_email=EMAIL_FROM,
            location_name=LOCATION["name"],
            analysis=analysis
        )
        
        if result.get("success"):
            print(f"  ✅ Email sent! ID: {result.get('id')}")
        else:
            print(f"  ❌ Email failed: {result.get('error')}")
            sys.exit(1)
    
    print("\n✨ Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather Analyst for Diving Club")
    parser.add_argument("--test", action="store_true", help="Test mode - print analysis without sending email")
    parser.add_argument("--no-email", action="store_true", help="Skip email sending")
    
    args = parser.parse_args()
    main(test_mode=args.test, no_email=args.no_email)
