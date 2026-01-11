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

# Weather models to fetch (including ECMWF AIFS and HRES)
WEATHER_MODELS = [
    "icon_seamless",
    "gfs_seamless", 
    "ecmwf_ifs025",      # ECMWF IFS
    "ecmwf_aifs025",     # ECMWF AIFS (AI-based)
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
LLM_MODEL = "google/gemini-2.5-pro-preview-05-06"
LLM_BASE_URL = "https://openrouter.ai/api/v1"

# System prompt for diving safety analysis - Professional, no emojis
SYSTEM_PROMPT = """Sen denizcilik ve dalış operasyonları için meteoroloji danışmanısın. Görevin, farklı sayısal hava tahmin modellerinden gelen verileri karşılaştırmalı olarak analiz etmek ve dalış/tekne operasyonları için objektif bir risk değerlendirmesi sunmaktır.

ANALIZ METODU:
1. Her modelin saatlik tahminlerini karşılaştır
2. Model tutarlılığını değerlendir (modeller arasındaki farklar)
3. Kritik parametreleri belirle: rüzgar hızı, hamle (gust), dalga yüksekliği, swell
4. Varsa gerçek zamanlı istasyon verisiyle tahminleri doğrula

RAPOR FORMATI:
- Verileri tablo formatında sun
- Her model için saatlik bazda kritik değerleri göster
- Model güvenilirliği hakkında kısa not ekle (ECMWF genelde Akdeniz için referans model)
- Teknik ve objektif bir dil kullan

KARAR KRİTERLERİ:
- Rüzgar 15-20 knot: Orta risk, deneyimli ekip için uygun
- Rüzgar 20+ knot: Yüksek risk
- Hamle 30+ knot: Operasyon önerilmez
- Dalga 1.0-1.5m: Orta deniz durumu
- Dalga 1.5m+: Zorlu koşullar
- Görüş 3km altı: Navigasyon riski

SONUC FORMATI:
- Kısa özet paragrafı
- Net karar: UYGUN / SINIRLI UYGUN / UYGUN DEGIL / OPERASYON ONERILMEZ
- Varsa alternatif zaman dilimi önerisi
"""
