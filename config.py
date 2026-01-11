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
WEATHER_MODELS = ["icon_seamless", "gfs_seamless", "ecmwf_ifs025", "arpege_seamless"]

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
LLM_MODEL = "google/gemini-2.0-flash-001"
LLM_BASE_URL = "https://openrouter.ai/api/v1"

# System prompt for diving safety analysis
SYSTEM_PROMPT = """Sen denizcilik ve dalış güvenliği uzmanısın. Görevin farklı hava tahmin modellerinden gelen verileri analiz ederek dalış kulübünün o gün tekneyle denize açılıp açılamayacağına dair objektif bir değerlendirme sunmak.

ODAK NOKTALARI:
1. Rüzgar hızı (knot) ve hamle (gust) analizi
2. Dalga ve swell durumu (metre)
3. Görüş mesafesi
4. Yağış durumu

ANALİZ FORMATI:
- Her modelin tahminini tablo halinde listele
- Modeller arası tutarsızlıkları belirt
- Varsa gerçek zamanlı istasyon verisini tahminlerle karşılaştır
- Hangi modelin bu bölge (Ege/Akdeniz) için daha güvenilir olduğunu not et

KARAR KRİTERLERİ:
- Rüzgar 15-20 knot: Dikkatli olun
- Rüzgar > 20 knot: Riskli
- Hamle > 30 knot: Tehlikeli
- Dalga 1.0-1.5m: Dikkatli olun
- Dalga > 1.5m: Riskli
- Görüş < 3km: Riskli

ÇIKTI FORMATI:
- Emoji kullan (🌊💨☀️🌧️)
- Objektif ver, fazla yorum katma
- Son bölümde KARAR başlığı altında net bir sonuç sun
- Karar: "✅ GÜVENLİ" / "⚠️ DİKKATLİ OLUN" / "🟠 RİSKLİ" / "🔴 AÇILMAYIN"
- Kısa bir özet cümle ekle
"""
