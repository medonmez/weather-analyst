"""
Weather Analyst Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Location: Kara Ada, Bodrum
LOCATION = {
    "name": "Kara Ada, Bodrum",
    "lat": 36.9710,
    "lon": 27.4575
}

# Weather models to fetch
WEATHER_MODELS = [
    "icon_seamless",
    "gfs_seamless", 
    "ecmwf_ifs025",      # ECMWF IFS
    "ecmwf_ifs04",       # ECMWF IFS HRES 9km
    "ecmwf_aifs025",     # ECMWF AIFS
    "arpege_seamless"
]

# Safety thresholds for diving operations
SAFETY_THRESHOLDS = {
    "wind_knots_warning": 15,
    "wind_knots_risky": 20,
    "wind_knots_dangerous": 30,
    "gust_knots_dangerous": 35,
    "wave_meters_warning": 1.0,
    "wave_meters_risky": 1.5,
    "wave_meters_dangerous": 2.0,
    "visibility_km_risky": 3
}

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
WINDY_API_KEY = os.getenv("WINDY_API_KEY")

# Email settings
EMAIL_TO = os.getenv("EMAIL_TO", "diving_club@example.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

# LLM settings
LLM_MODEL = "google/gemini-3-pro-preview"
LLM_BASE_URL = "https://openrouter.ai/api/v1"

# System prompt - neutral, no model bias
SYSTEM_PROMPT = """Sen denizcilik ve dalis operasyonlari icin meteoroloji danismanisin. 

Gorev: Farkli hava tahmin modellerinden gelen verileri analiz ederek dalis kulubu icin tekne operasyonu risk degerlendirmesi yap.

Analiz edilecek parametreler:
- Ruzgar hizi (knot) ve hamle (gust)
- Dalga yuksekligi ve swell
- Gorus mesafesi
- Yagis durumu

Karar kriterleri:
- Ruzgar 15-20 knot: Orta risk
- Ruzgar 20+ knot: Yuksek risk
- Hamle 30+ knot: Operasyon onerilmez
- Dalga 1.0-1.5m: Orta deniz durumu
- Dalga 1.5m+: Zorlu kosullar

Cikti:
- Modelleri karsilastir
- Tutarsizliklari belirt
- Net karar ver: UYGUN / SINIRLI UYGUN / UYGUN DEGIL / OPERASYON ONERILMEZ
- Kisa ozet ekle
"""
