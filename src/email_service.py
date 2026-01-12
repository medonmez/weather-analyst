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
    """
    if not api_key:
        return {"error": "Resend API key not configured"}
    
    resend.api_key = api_key
    
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    report_type = "Bugün" if forecast_day == "today" else "Yarın"
    
    if not subject:
        subject = f"Bodrum Hava Durumu Raporu - {report_type} - {date_str}"
    
    html_content = generate_html_email(analysis)
    
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


def generate_html_email(analysis: str) -> str:
    """Generate clean HTML email from markdown analysis - no extra header"""
    
    # Convert markdown to HTML
    html_analysis = markdown_to_html(analysis)
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            line-height: 1.7;
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
        h1 {{
            color: #1a365d;
            font-size: 20px;
            margin-top: 0;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #1a365d;
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
        ul {{
            margin: 8px 0;
            padding-left: 24px;
        }}
        li {{
            margin: 4px 0;
        }}
        strong {{
            font-weight: 600;
        }}
        p {{
            margin: 8px 0;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: #718096;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            {html_analysis}
        </div>
        <div class="footer">
            Bu rapor otomatik olarak olusturulmustur.<br>
            Veri Kaynaklari: Open-Meteo (ECMWF, ICON-EU, GFS, Meteo-France)<br>
            Analiz: Gemini AI
        </div>
    </div>
</body>
</html>"""


def markdown_to_html(md: str) -> str:
    """Convert markdown to HTML with proper bullet point support"""
    import re
    
    html = md
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Process lines for tables and bullet points
    lines = html.split('\n')
    in_table = False
    in_list = False
    result_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Table handling
        if '|' in line and stripped.startswith('|'):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if not in_table:
                result_lines.append('<table>')
                in_table = True
            
            # Skip separator lines
            if re.match(r'\|[\s\-:|]+\|', line):
                continue
            
            cells = [c.strip() for c in line.split('|')[1:-1]]
            row_type = 'th' if result_lines[-1] == '<table>' else 'td'
            row = '<tr>' + ''.join(f'<{row_type}>{c}</{row_type}>' for c in cells) + '</tr>'
            result_lines.append(row)
        
        # Bullet point handling (* or -)
        elif stripped.startswith('* ') or stripped.startswith('- '):
            if in_table:
                result_lines.append('</table>')
                in_table = False
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            
            # Remove the bullet marker and add li tag
            content = stripped[2:]
            result_lines.append(f'<li>{content}</li>')
        
        else:
            if in_table:
                result_lines.append('</table>')
                in_table = False
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)
    
    if in_table:
        result_lines.append('</table>')
    if in_list:
        result_lines.append('</ul>')
    
    html = '\n'.join(result_lines)
    
    # Line breaks - but not inside lists or tables
    html = re.sub(r'\n\n(?![<])', '</p><p>', html)
    
    # Wrap in paragraph if not starting with HTML tag
    if not html.strip().startswith('<'):
        html = '<p>' + html + '</p>'
    
    return html
