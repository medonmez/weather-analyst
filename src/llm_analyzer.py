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
        model: Model name (e.g., google/gemini-2.0-flash-001)
        system_prompt: System prompt for analysis
        location_name: Name of location
    
    Returns:
        LLM-generated analysis text
    """
    if not api_key:
        return "❌ OpenRouter API key not configured"
    
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
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ LLM API Error: {str(e)}"


def build_data_prompt(
    weather_data: Dict[str, Any],
    marine_data: Dict[str, Any],
    station_data: Dict[str, Any],
    location_name: str
) -> str:
    """Build the user prompt with all weather data"""
    
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    time_of_day = "Sabah" if now.hour < 12 else "Akşam"
    
    prompt = f"""# Hava Durumu Analizi Talebi

**Konum:** {location_name}
**Tarih:** {date_str}
**Rapor Tipi:** {time_of_day} Raporu
**Analiz Saatleri:** 08:00 - 18:00

---

## 📊 HAVA TAHMİN MODELLERİ

"""
    
    # Add weather model data
    for model_id, data in weather_data.items():
        if "error" in data:
            prompt += f"### {model_id}\n❌ Veri alınamadı: {data['error']}\n\n"
            continue
        
        summary = data.get("summary", {})
        from src.open_meteo_weather import get_model_display_name
        model_name = get_model_display_name(model_id)
        
        prompt += f"""### {model_name}
| Parametre | Değer |
|-----------|-------|
| Ortalama Rüzgar | {summary.get('avg_wind_knots', 'N/A')} knot |
| Maksimum Rüzgar | {summary.get('max_wind_knots', 'N/A')} knot |
| Maksimum Hamle | {summary.get('max_gust_knots', 'N/A')} knot |
| Ortalama Sıcaklık | {summary.get('avg_temp', 'N/A')}°C |
| Maks Yağış Olasılığı | %{summary.get('max_precip_prob', 'N/A')} |

"""
    
    # Add marine data
    prompt += "---\n\n## 🌊 DENİZ DURUMU\n\n"
    
    if "error" in marine_data:
        prompt += f"❌ Veri alınamadı: {marine_data['error']}\n\n"
    else:
        marine_summary = marine_data.get("summary", {})
        prompt += f"""| Parametre | Değer |
|-----------|-------|
| Ortalama Dalga | {marine_summary.get('avg_wave_height', 'N/A')} m |
| Maksimum Dalga | {marine_summary.get('max_wave_height', 'N/A')} m |
| Ortalama Swell | {marine_summary.get('avg_swell_height', 'N/A')} m |
| Maksimum Swell | {marine_summary.get('max_swell_height', 'N/A')} m |
| Swell Periyodu | {marine_summary.get('avg_swell_period', 'N/A')} s |
| Swell Yönü | {marine_summary.get('primary_swell_direction', 'N/A')} |

"""
    
    # Add station data
    prompt += "---\n\n## 📡 GERÇEK ZAMANLI İSTASYON VERİSİ\n\n"
    
    if not station_data.get("available"):
        prompt += f"ℹ️ {station_data.get('message', 'İstasyon verisi mevcut değil')}\n\n"
    else:
        measurements = station_data.get("measurements", {})
        prompt += f"""**İstasyon:** {station_data.get('station_name', 'Unknown')} ({station_data.get('distance_km', '?')} km uzaklıkta)

| Parametre | Güncel Değer |
|-----------|--------------|
| Rüzgar | {measurements.get('wind_knots', 'N/A')} knot |
| Hamle | {measurements.get('gust_knots', 'N/A')} knot |
| Rüzgar Yönü | {measurements.get('wind_direction', 'N/A')}° |
| Sıcaklık | {measurements.get('temperature_c', 'N/A')}°C |
| Basınç | {measurements.get('pressure_hpa', 'N/A')} hPa |

"""
    
    prompt += """---

## 📝 ANALİZ TALEBİ

Lütfen yukarıdaki verileri analiz et ve:
1. Her modelin tahminlerini karşılaştır
2. Deniz durumunu değerlendir
3. Varsa gerçek zamanlı veriyi tahminlerle karşılaştır
4. Dalış kulübünün bugün tekneyle açılıp açılmaması konusunda net bir karar ver
"""
    
    return prompt
