"""
LLM Analyzer using OpenRouter API
Analyzes weather data and generates diving safety report
"""
from openai import OpenAI
from typing import Dict, Any
from datetime import datetime


def analyze_weather(
    weather_data: Dict[str, Any],
    marine_data: Dict[str, Any],
    station_data: Dict[str, Any],
    api_key: str,
    model: str,
    system_prompt: str,
    location_name: str
) -> str:
    """
    Send weather data to LLM for analysis
    
    Args:
        weather_data: Multi-model weather forecasts
        marine_data: Marine/wave data
        station_data: Real-time station data
        api_key: OpenRouter API key
        model: Model name
        system_prompt: System prompt for analysis
        location_name: Name of location
    
    Returns:
        LLM-generated analysis text
    """
    if not api_key:
        return "HATA: OpenRouter API key not configured"
    
    # Build the data prompt
    user_prompt = build_data_prompt(weather_data, marine_data, station_data, location_name)
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"HATA: LLM API Error: {str(e)}"


def build_data_prompt(
    weather_data: Dict[str, Any],
    marine_data: Dict[str, Any],
    station_data: Dict[str, Any],
    location_name: str
) -> str:
    """Build the user prompt with hourly weather data tables"""
    
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    time_of_day = "Sabah" if now.hour < 12 else "Aksam"
    
    prompt = f"""# Meteoroloji Analiz Talebi

Konum: {location_name}
Tarih: {date_str}
Rapor Tipi: {time_of_day} Raporu
Analiz Saatleri: 08:00 - 18:00

---

## HAVA TAHMIN MODELLERI - SAATLIK VERILER

"""
    
    # Add hourly weather data for each model
    for model_id, data in weather_data.items():
        if "error" in data:
            prompt += f"### {model_id}\nVeri alinamadi: {data['error']}\n\n"
            continue
        
        from src.open_meteo_weather import get_model_display_name
        model_name = get_model_display_name(model_id)
        
        times = data.get("times", [])
        wind_speeds = data.get("wind_speed_knots", [])
        wind_gusts = data.get("wind_gusts_knots", [])
        wind_dirs = data.get("wind_direction", [])
        temps = data.get("temperature", [])
        
        prompt += f"### {model_name}\n"
        prompt += "| Saat | Ruzgar (knot) | Hamle (knot) | Yon | Sicaklik |\n"
        prompt += "|------|---------------|--------------|-----|----------|\n"
        
        for i in range(min(len(times), 11)):
            hour = times[i].split("T")[1][:5] if i < len(times) else "-"
            wind = f"{wind_speeds[i]:.1f}" if i < len(wind_speeds) else "-"
            gust = f"{wind_gusts[i]:.1f}" if i < len(wind_gusts) else "-"
            direction = f"{wind_dirs[i]:.0f}" if i < len(wind_dirs) else "-"
            temp = f"{temps[i]:.1f}" if i < len(temps) else "-"
            prompt += f"| {hour} | {wind} | {gust} | {direction} | {temp} |\n"
        
        # Add summary
        summary = data.get("summary", {})
        prompt += f"\nOzet: Ort. {summary.get('avg_wind_knots', 'N/A')} knot, "
        prompt += f"Maks. {summary.get('max_wind_knots', 'N/A')} knot, "
        prompt += f"Hamle Maks. {summary.get('max_gust_knots', 'N/A')} knot\n\n"
    
    # Add marine data with hourly details
    prompt += "---\n\n## DENIZ DURUMU - SAATLIK VERILER\n\n"
    
    if "error" in marine_data:
        prompt += f"Veri alinamadi: {marine_data['error']}\n\n"
    else:
        times = marine_data.get("times", [])
        wave_heights = marine_data.get("wave_height", [])
        swell_heights = marine_data.get("swell_wave_height", [])
        swell_periods = marine_data.get("swell_wave_period", [])
        
        prompt += "| Saat | Dalga (m) | Swell (m) | Periyot (s) |\n"
        prompt += "|------|-----------|-----------|-------------|\n"
        
        for i in range(min(len(times), 11)):
            hour = times[i].split("T")[1][:5] if i < len(times) else "-"
            wave = f"{wave_heights[i]:.2f}" if i < len(wave_heights) and wave_heights[i] else "-"
            swell = f"{swell_heights[i]:.2f}" if i < len(swell_heights) and swell_heights[i] else "-"
            period = f"{swell_periods[i]:.1f}" if i < len(swell_periods) and swell_periods[i] else "-"
            prompt += f"| {hour} | {wave} | {swell} | {period} |\n"
        
        marine_summary = marine_data.get("summary", {})
        prompt += f"\nOzet: Dalga Ort. {marine_summary.get('avg_wave_height', 'N/A')}m, "
        prompt += f"Maks. {marine_summary.get('max_wave_height', 'N/A')}m | "
        prompt += f"Swell Ort. {marine_summary.get('avg_swell_height', 'N/A')}m, "
        prompt += f"Yon: {marine_summary.get('primary_swell_direction', 'N/A')}\n\n"
    
    # Add station data
    prompt += "---\n\n## GERCEK ZAMANLI ISTASYON VERISI\n\n"
    
    if not station_data.get("available"):
        prompt += f"Not: {station_data.get('message', 'Istasyon verisi mevcut degil')}\n\n"
    else:
        measurements = station_data.get("measurements", {})
        prompt += f"Istasyon: {station_data.get('station_name', 'Unknown')} ({station_data.get('distance_km', '?')} km uzaklikta)\n\n"
        prompt += "| Parametre | Guncel Deger |\n"
        prompt += "|-----------|---------------|\n"
        prompt += f"| Ruzgar | {measurements.get('wind_knots', 'N/A')} knot |\n"
        prompt += f"| Hamle | {measurements.get('gust_knots', 'N/A')} knot |\n"
        prompt += f"| Ruzgar Yonu | {measurements.get('wind_direction', 'N/A')} |\n"
        prompt += f"| Sicaklik | {measurements.get('temperature_c', 'N/A')} C |\n"
        prompt += f"| Basinc | {measurements.get('pressure_hpa', 'N/A')} hPa |\n\n"
    
    prompt += """---

## ANALIZ TALEBI

Yukaridaki saatlik verileri analiz ederek:
1. Modellerin tutarliligini degerlendir
2. Kritik saat dilimlerini belirle
3. Deniz durumu ile ruzgar iliskisini analiz et
4. Tekne operasyonu icin net bir karar ver
"""
    
    return prompt
