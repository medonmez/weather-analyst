"""
LLM Analyzer using OpenRouter API
Sends raw JSON data to LLM for analysis
"""
import json
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
    Send raw weather data to LLM for analysis
    """
    if not api_key:
        return "HATA: OpenRouter API key not configured"
    
    # Prepare raw data as JSON
    raw_data = {
        "location": location_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "weather_models": weather_data,
        "marine_data": marine_data,
        "station_data": station_data
    }
    
    # Send raw JSON to LLM
    user_message = json.dumps(raw_data, indent=2, ensure_ascii=False, default=str)
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"HATA: LLM API Error: {str(e)}"
