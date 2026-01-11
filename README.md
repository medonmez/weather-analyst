# Weather Analyst - Dalış Kulübü

Bodrum/Kara Ada için dalış operasyonları güvenlik analiz sistemi.

## Özellikler

- 🌊 **Open-Meteo Marine API** - Dalga, swell analizi
- 💨 **Open-Meteo Weather API** - Rüzgar, hava (ICON, GFS, ECMWF, ARPEGE)
- 📡 **Windy Stations** - Gerçek zamanlı ölçümler
- 🤖 **LLM Analizi** - OpenRouter + Gemini 3 Pro
- 📧 **Email** - Resend API ile sabah/akşam raporları
- ⚡ **Serverless** - GitHub Actions ile çalışır

## Kurulum

1. Repository fork/clone
2. API key'leri al:
   - [OpenRouter](https://openrouter.ai)
   - [Resend](https://resend.com)
   - [Windy Stations](https://stations.windy.com)
3. GitHub Secrets'a ekle:
   - `OPENROUTER_API_KEY`
   - `RESEND_API_KEY`
   - `WINDY_API_KEY`
   - `EMAIL_TO`

## Manuel Çalıştırma

```bash
cp .env.example .env
# .env dosyasını düzenle
python main.py
```

## Zamanlama

GitHub Actions ile otomatik:
- Sabah 07:00 (TR)
- Akşam 19:00 (TR)
