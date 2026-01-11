"""
Email Service using Resend API
Sends weather reports via email with JSON data attachment
"""
import resend
import json
import base64
from datetime import datetime
from typing import Optional, Dict, Any


def send_report_email(
    api_key: str,
    to_email: str,
    from_email: str,
    location_name: str,
    analysis: str,
    raw_data: Optional[Dict[str, Any]] = None,
    chart_bytes: Optional[bytes] = None,
    table_bytes: Optional[bytes] = None,
    subject: Optional[str] = None,
    forecast_day: str = "today"
) -> dict:
    """
    Send weather analysis report via Resend with JSON, chart, and table attachments
    
    Args:
        api_key: Resend API key
        to_email: Recipient email
        from_email: Sender email
        location_name: Location name for subject
        analysis: LLM analysis text
        raw_data: Raw weather data to attach as JSON
        chart_bytes: PNG chart bytes
        table_bytes: PNG table bytes
        subject: Optional custom subject
        forecast_day: "today" or "tomorrow"
    
    Returns:
        Resend API response
    """
    if not api_key:
        return {"error": "Resend API key not configured"}
    
    resend.api_key = api_key
    
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    report_type = "Bugun" if forecast_day == "today" else "Yarin"
    
    if not subject:
        subject = f"{location_name} Raporu - {report_type} - {date_str}"
    
    html_content = generate_html_email(analysis, location_name, date_str, report_type)
    
    # Parse comma-separated emails into list
    if isinstance(to_email, str):
        email_list = [e.strip() for e in to_email.split(',') if e.strip()]
    else:
        email_list = [to_email]
    
    # Prepare email payload
    email_payload = {
        "from": from_email,
        "to": email_list,
        "subject": subject,
        "html": html_content
    }
    
    # Prepare attachments
    attachments = []
    
    # Add JSON attachment if raw_data provided
    if raw_data:
        json_str = json.dumps(raw_data, indent=2, ensure_ascii=False, default=str)
        json_bytes = json_str.encode('utf-8')
        json_base64 = base64.b64encode(json_bytes).decode('utf-8')
        
        attachments.append({
            "filename": f"weather_data_{now.strftime('%Y%m%d_%H%M')}.json",
            "content": json_base64
        })
    
    # Add chart PNG if provided
    if chart_bytes:
        chart_base64 = base64.b64encode(chart_bytes).decode('utf-8')
        attachments.append({
            "filename": f"weather_chart_{now.strftime('%Y%m%d_%H%M')}.png",
            "content": chart_base64
        })
    
    # Add table PNG if provided
    if table_bytes:
        table_base64 = base64.b64encode(table_bytes).decode('utf-8')
        attachments.append({
            "filename": f"weather_table_{now.strftime('%Y%m%d_%H%M')}.png",
            "content": table_base64
        })
    
    if attachments:
        email_payload["attachments"] = attachments
    
    try:
        response = resend.Emails.send(email_payload)
        return {"success": True, "id": response.get("id")}
        
    except Exception as e:
        return {"error": str(e)}


def generate_html_email(analysis: str, location: str, date: str, time_of_day: str) -> str:
    """Generate professional HTML email from markdown analysis"""
    
    # Convert markdown to basic HTML
    html_analysis = markdown_to_html(analysis)
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: #ffffff;
            border-radius: 8px;
            padding: 32px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            border: 1px solid #e1e5e9;
        }}
        .header {{
            border-bottom: 2px solid #1a365d;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            color: #1a365d;
            margin: 0;
            font-size: 22px;
            font-weight: 600;
        }}
        .header .subtitle {{
            color: #4a5568;
            font-size: 14px;
            margin-top: 4px;
        }}
        .content {{
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 13px;
        }}
        th, td {{
            padding: 8px 12px;
            text-align: left;
            border: 1px solid #e2e8f0;
        }}
        th {{
            background: #f7fafc;
            font-weight: 600;
            color: #2d3748;
        }}
        tr:nth-child(even) {{
            background: #f7fafc;
        }}
        h2 {{
            color: #1a365d;
            font-size: 16px;
            margin-top: 28px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }}
        h3 {{
            color: #2d3748;
            font-size: 14px;
            margin-top: 20px;
            margin-bottom: 8px;
        }}
        .decision {{
            padding: 16px;
            margin: 24px 0;
            border-radius: 6px;
            font-weight: 600;
        }}
        .decision-uygun {{
            background: #c6f6d5;
            color: #22543d;
            border-left: 4px solid #38a169;
        }}
        .decision-sinirli {{
            background: #fefcbf;
            color: #744210;
            border-left: 4px solid #d69e2e;
        }}
        .decision-degil {{
            background: #fed7d7;
            color: #742a2a;
            border-left: 4px solid #e53e3e;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: #718096;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
        }}
        strong {{
            font-weight: 600;
        }}
        p {{
            margin: 8px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{location} - Meteoroloji Raporu</h1>
            <div class="subtitle">{date} | {time_of_day} Analizi</div>
        </div>
        <div class="content">
            {html_analysis}
        </div>
        <div class="footer">
            Bu rapor otomatik olarak olusturulmustur.<br>
            Veri Kaynaklari: Open-Meteo (ECMWF, ICON, GFS, ARPEGE), Windy Stations<br>
            Analiz: Google Gemini AI | JSON verisi ekte mevcuttur.
        </div>
    </div>
</body>
</html>"""


def markdown_to_html(md: str) -> str:
    """Convert markdown to HTML"""
    import re
    
    html = md
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Tables
    lines = html.split('\n')
    in_table = False
    result_lines = []
    
    for line in lines:
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                result_lines.append('<table>')
                in_table = True
            
            # Skip separator lines
            if re.match(r'\|[\s\-:|]+\|', line):
                continue
            
            cells = [c.strip() for c in line.split('|')[1:-1]]
            row_type = 'th' if not any('<table>' in l for l in result_lines[-5:]) or result_lines[-1] == '<table>' else 'td'
            row = '<tr>' + ''.join(f'<{row_type}>{c}</{row_type}>' for c in cells) + '</tr>'
            result_lines.append(row)
        else:
            if in_table:
                result_lines.append('</table>')
                in_table = False
            result_lines.append(line)
    
    if in_table:
        result_lines.append('</table>')
    
    html = '\n'.join(result_lines)
    
    # Line breaks
    html = html.replace('\n\n', '</p><p>')
    html = '<p>' + html + '</p>'
    
    return html
