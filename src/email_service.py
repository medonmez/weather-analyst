"""
Email Service using Resend API
Sends weather reports via email
"""
import resend
from datetime import datetime
from typing import Optional


def send_report_email(
    api_key: str,
    to_email: str,
    from_email: str,
    location_name: str,
    analysis: str,
    subject: Optional[str] = None
) -> dict:
    """
    Send weather analysis report via Resend
    
    Args:
        api_key: Resend API key
        to_email: Recipient email
        from_email: Sender email
        location_name: Location name for subject
        analysis: LLM analysis text
        subject: Optional custom subject
    
    Returns:
        Resend API response
    """
    if not api_key:
        return {"error": "Resend API key not configured"}
    
    resend.api_key = api_key
    
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    time_of_day = "Sabah" if now.hour < 12 else "Akşam"
    
    if not subject:
        subject = f"🌊 {location_name} Dalış Raporu - {date_str} {time_of_day}"
    
    html_content = generate_html_email(analysis, location_name, date_str, time_of_day)
    
    try:
        response = resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        })
        return {"success": True, "id": response.get("id")}
        
    except Exception as e:
        return {"error": str(e)}


def generate_html_email(analysis: str, location: str, date: str, time_of_day: str) -> str:
    """Generate HTML email from markdown analysis"""
    
    # Convert markdown to basic HTML
    html_analysis = markdown_to_html(analysis)
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .header h1 {{
            color: #0066cc;
            margin: 0;
            font-size: 24px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .content {{
            font-size: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .decision {{
            text-align: center;
            padding: 20px;
            margin: 25px 0;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        }}
        .safe {{
            background: #d4edda;
            color: #155724;
        }}
        .caution {{
            background: #fff3cd;
            color: #856404;
        }}
        .risky {{
            background: #ffe0b2;
            color: #e65100;
        }}
        .danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        h2, h3 {{
            color: #0066cc;
            margin-top: 25px;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌊 {location} Dalış Raporu</h1>
            <div class="subtitle">{date} - {time_of_day} Analizi</div>
        </div>
        <div class="content">
            {html_analysis}
        </div>
        <div class="footer">
            Bu rapor otomatik olarak oluşturulmuştur.<br>
            Veriler: Open-Meteo, Windy Stations | Analiz: Gemini AI
        </div>
    </div>
</body>
</html>"""


def markdown_to_html(md: str) -> str:
    """Simple markdown to HTML converter"""
    import re
    
    html = md
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Tables - basic conversion
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
