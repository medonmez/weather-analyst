"""
Weather Visualization Module
Creates Windguru-style charts and tables for weather data
"""
import io
import base64
from typing import Dict, Any, List, Tuple
from datetime import datetime

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# Windguru-style color scheme for wind speeds (knots)
def get_wind_color(speed: float) -> str:
    """Get Windguru-style color for wind speed in knots"""
    if speed < 5:
        return '#E8F5E9'    # Very light green
    elif speed < 10:
        return '#C8E6C9'    # Light green
    elif speed < 15:
        return '#A5D6A7'    # Green
    elif speed < 20:
        return '#FFEB3B'    # Yellow
    elif speed < 25:
        return '#FFC107'    # Amber
    elif speed < 30:
        return '#FF9800'    # Orange
    elif speed < 35:
        return '#FF5722'    # Deep Orange
    elif speed < 40:
        return '#F44336'    # Red
    elif speed < 45:
        return '#E91E63'    # Pink
    else:
        return '#9C27B0'    # Purple (extreme)


def get_wave_color(height: float) -> str:
    """Get color for wave height in meters"""
    if height < 0.3:
        return '#E3F2FD'
    elif height < 0.5:
        return '#BBDEFB'
    elif height < 0.8:
        return '#90CAF9'
    elif height < 1.0:
        return '#64B5F6'
    elif height < 1.5:
        return '#42A5F5'
    elif height < 2.0:
        return '#2196F3'
    else:
        return '#1565C0'


def get_temp_color(temp: float) -> str:
    """Get color for temperature"""
    if temp < 10:
        return '#90CAF9'
    elif temp < 15:
        return '#E1F5FE'
    elif temp < 20:
        return '#FFF9C4'
    elif temp < 25:
        return '#FFEB3B'
    elif temp < 30:
        return '#FF9800'
    else:
        return '#FF5722'


def get_precip_color(precip: float) -> str:
    """Get color for precipitation in mm"""
    if precip < 0.1:
        return '#FAFAFA'    # Almost white - no rain
    elif precip < 1:
        return '#E1F5FE'    # Very light blue
    elif precip < 3:
        return '#81D4FA'    # Light blue
    elif precip < 5:
        return '#29B6F6'    # Blue
    elif precip < 10:
        return '#0288D1'    # Dark blue
    else:
        return '#01579B'    # Very dark blue


def get_direction_arrow(degrees: float) -> str:
    """Get arrow character for wind direction"""
    arrows = ['↓', '↙', '←', '↖', '↑', '↗', '→', '↘']
    index = round(degrees / 45) % 8
    return arrows[index]


def get_direction_name(degrees: float) -> str:
    """Get direction name"""
    dirs = ['K', 'KD', 'D', 'GD', 'G', 'GB', 'B', 'KB']
    index = round(degrees / 45) % 8
    return dirs[index]


def create_windguru_table(weather_data: Dict[str, Any], marine_data: Dict[str, Any], target_date: str) -> bytes:
    """
    Create a Windguru-style colored table with EACH MODEL having its own complete section
    
    Args:
        weather_data: Weather data from multiple models
        marine_data: Marine/wave data
        target_date: Target date
    
    Returns:
        PNG image as bytes (tall vertical layout)
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    # Get hours from first valid model
    hours = []
    valid_models = []
    for model_id, data in weather_data.items():
        if "times" in data and data["times"]:
            if not hours:
                hours = [t.split("T")[1][:5] for t in data["times"]]
            valid_models.append((model_id, data))
    
    if not hours or not valid_models:
        return None
    
    n_hours = len(hours)
    n_models = len(valid_models)
    rows_per_model = 6  # Wind, Gust, Direction, Temp, Precip, Visibility
    
    # Calculate figure size - tall vertical
    fig_width = max(14, n_hours * 0.9)
    fig_height = 2 + n_models * (rows_per_model * 0.5 + 1)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, n_hours + 1.5)
    total_rows = 2 + n_models * (rows_per_model + 1)
    ax.set_ylim(0, total_rows)
    ax.axis('off')
    fig.patch.set_facecolor('#1a1a2e')
    
    # Title
    current_y = total_rows - 0.5
    ax.text(n_hours/2 + 1, current_y, f'HAVA DURUMU TAHMİNİ - {target_date}', 
            fontsize=16, fontweight='bold', ha='center', va='center', color='white')
    current_y -= 0.6
    ax.text(n_hours/2 + 1, current_y, 'Kara Ada, Bodrum | Saatlik Detaylı Tablo', 
            fontsize=11, ha='center', va='center', color='#BDC3C7')
    current_y -= 1
    
    # Process each model
    for model_id, data in valid_models:
        model_name = get_model_display_name(model_id)
        
        # Model header
        ax.add_patch(plt.Rectangle((0, current_y - 0.4), n_hours + 1.5, 0.8, 
                                   facecolor='#3498DB', edgecolor='#2C3E50', linewidth=2))
        ax.text(n_hours/2 + 0.75, current_y, f'{model_name}', 
                fontsize=12, fontweight='bold', ha='center', va='center', color='white')
        current_y -= 0.8
        
        # Hour header row
        ax.add_patch(plt.Rectangle((0, current_y - 0.35), 1.5, 0.7, facecolor='#34495E', edgecolor='#2C3E50'))
        ax.text(0.75, current_y, 'Saat', fontsize=8, fontweight='bold', ha='center', va='center', color='white')
        for i, hour in enumerate(hours):
            ax.add_patch(plt.Rectangle((i + 1.5, current_y - 0.35), 1, 0.7, facecolor='#34495E', edgecolor='#2C3E50'))
            ax.text(i + 2, current_y, hour, fontsize=8, fontweight='bold', ha='center', va='center', color='white')
        current_y -= 0.7
        
        # Row 1: Wind Speed
        _draw_data_row(ax, current_y, 'Rüzgar\n(knot)', data.get('wind_speed_knots', []), 
                      n_hours, '#27AE60', get_wind_color, '{:.0f}')
        current_y -= 0.7
        
        # Row 2: Wind Gusts  
        _draw_data_row(ax, current_y, 'Hamle\n(knot)', data.get('wind_gusts_knots', []),
                      n_hours, '#E74C3C', get_wind_color, '{:.0f}')
        current_y -= 0.7
        
        # Row 3: Wind Direction
        dirs = data.get('wind_direction_deg', [])
        ax.add_patch(plt.Rectangle((0, current_y - 0.35), 1.5, 0.7, facecolor='#9B59B6', edgecolor='#2C3E50'))
        ax.text(0.75, current_y, 'Yön', fontsize=8, fontweight='bold', ha='center', va='center', color='white')
        for i in range(n_hours):
            ax.add_patch(plt.Rectangle((i + 1.5, current_y - 0.35), 1, 0.7, facecolor='#ECF0F1', edgecolor='#2C3E50'))
            if i < len(dirs) and dirs[i] is not None:
                arrow = get_direction_arrow(dirs[i])
                ax.text(i + 2, current_y, arrow, fontsize=14, ha='center', va='center', color='#2C3E50')
        current_y -= 0.7
        
        # Row 4: Temperature
        _draw_data_row(ax, current_y, 'Sıcaklık\n(°C)', data.get('temperature_c', []),
                      n_hours, '#FF5722', get_temp_color, '{:.0f}')
        current_y -= 0.7
        
        # Row 5: Precipitation
        _draw_data_row(ax, current_y, 'Yağış\n(mm)', data.get('precipitation_mm', []),
                      n_hours, '#0288D1', get_precip_color, '{:.1f}')
        current_y -= 0.7
        
        # Row 6: Visibility
        vis = data.get('visibility_m', [])
        ax.add_patch(plt.Rectangle((0, current_y - 0.35), 1.5, 0.7, facecolor='#607D8B', edgecolor='#2C3E50'))
        ax.text(0.75, current_y, 'Görüş\n(km)', fontsize=7, fontweight='bold', ha='center', va='center', color='white')
        for i in range(n_hours):
            ax.add_patch(plt.Rectangle((i + 1.5, current_y - 0.35), 1, 0.7, facecolor='#ECEFF1', edgecolor='#2C3E50'))
            if i < len(vis) and vis[i] is not None:
                vis_km = vis[i] / 1000
                ax.text(i + 2, current_y, f'{vis_km:.0f}', fontsize=8, ha='center', va='center', color='#37474F')
        current_y -= 1.2  # Extra space between models
    
    # Marine data section
    if "wave_height_m" in marine_data and marine_data["wave_height_m"]:
        ax.add_patch(plt.Rectangle((0, current_y - 0.4), n_hours + 1.5, 0.8, 
                                   facecolor='#00BCD4', edgecolor='#2C3E50', linewidth=2))
        ax.text(n_hours/2 + 0.75, current_y, 'DENIZ DURUMU', 
                fontsize=12, fontweight='bold', ha='center', va='center', color='white')
        current_y -= 0.8
        
        # Hour header
        ax.add_patch(plt.Rectangle((0, current_y - 0.35), 1.5, 0.7, facecolor='#34495E', edgecolor='#2C3E50'))
        ax.text(0.75, current_y, 'Saat', fontsize=8, fontweight='bold', ha='center', va='center', color='white')
        marine_hours = marine_data.get('times', [])
        for i in range(min(n_hours, len(marine_hours))):
            hour = marine_hours[i].split("T")[1][:5] if i < len(marine_hours) else hours[i]
            ax.add_patch(plt.Rectangle((i + 1.5, current_y - 0.35), 1, 0.7, facecolor='#34495E', edgecolor='#2C3E50'))
            ax.text(i + 2, current_y, hour, fontsize=8, fontweight='bold', ha='center', va='center', color='white')
        current_y -= 0.7
        
        # Wave height
        _draw_data_row(ax, current_y, 'Dalga\n(m)', marine_data.get('wave_height_m', []),
                      n_hours, '#00BCD4', get_wave_color, '{:.1f}', text_color='#0D47A1')
        current_y -= 0.7
        
        # Wave direction (arrows)
        wave_dirs = marine_data.get('wave_direction_deg', [])
        ax.add_patch(plt.Rectangle((0, current_y - 0.35), 1.5, 0.7, facecolor='#0097A7', edgecolor='#2C3E50'))
        ax.text(0.75, current_y, 'Dalga\nYönü', fontsize=7, fontweight='bold', ha='center', va='center', color='white')
        for i in range(n_hours):
            ax.add_patch(plt.Rectangle((i + 1.5, current_y - 0.35), 1, 0.7, facecolor='#E0F7FA', edgecolor='#2C3E50'))
            if i < len(wave_dirs) and wave_dirs[i] is not None:
                arrow = get_direction_arrow(wave_dirs[i])
                ax.text(i + 2, current_y, arrow, fontsize=14, ha='center', va='center', color='#006064')
        current_y -= 0.7
        
        # Swell height
        _draw_data_row(ax, current_y, 'Swell\n(m)', marine_data.get('swell_wave_height_m', []),
                      n_hours, '#7C4DFF', get_wave_color, '{:.1f}', text_color='#311B92')
        current_y -= 0.7
        
        # Swell direction (arrows)
        swell_dirs = marine_data.get('swell_wave_direction_deg', [])
        ax.add_patch(plt.Rectangle((0, current_y - 0.35), 1.5, 0.7, facecolor='#651FFF', edgecolor='#2C3E50'))
        ax.text(0.75, current_y, 'Swell\nYönü', fontsize=7, fontweight='bold', ha='center', va='center', color='white')
        for i in range(n_hours):
            ax.add_patch(plt.Rectangle((i + 1.5, current_y - 0.35), 1, 0.7, facecolor='#EDE7F6', edgecolor='#2C3E50'))
            if i < len(swell_dirs) and swell_dirs[i] is not None:
                arrow = get_direction_arrow(swell_dirs[i])
                ax.text(i + 2, current_y, arrow, fontsize=14, ha='center', va='center', color='#4527A0')
    
    ax.set_ylim(current_y - 1, total_rows)
    
    plt.tight_layout()
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor='#1a1a2e', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    table_bytes = buf.getvalue()
    plt.close()
    
    return table_bytes


def _draw_data_row(ax, y: float, label: str, values: list, n_hours: int, 
                  header_color: str, color_func, fmt: str, text_color: str = None):
    """Helper function to draw a data row"""
    ax.add_patch(plt.Rectangle((0, y - 0.35), 1.5, 0.7, facecolor=header_color, edgecolor='#2C3E50'))
    ax.text(0.75, y, label, fontsize=7, fontweight='bold', ha='center', va='center', color='white')
    
    for i in range(n_hours):
        if i < len(values) and values[i] is not None:
            val = values[i]
            color = color_func(val)
            txt_color = text_color if text_color else ('white' if val > 35 else '#333333')
            ax.add_patch(plt.Rectangle((i + 1.5, y - 0.35), 1, 0.7, facecolor=color, edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 2, y, fmt.format(val), fontsize=8, fontweight='bold', ha='center', va='center', color=txt_color)
        else:
            ax.add_patch(plt.Rectangle((i + 1.5, y - 0.35), 1, 0.7, facecolor='#BDBDBD', edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 2, y, '-', fontsize=8, ha='center', va='center', color='#757575')


def create_windguru_chart(weather_data: Dict[str, Any], marine_data: Dict[str, Any], target_date: str) -> bytes:
    """Create a Windguru-style weather chart"""
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    plt.style.use('dark_background')
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1.5, 1, 1]})
    fig.patch.set_facecolor('#1a1a2e')
    
    hours = []
    for model_id, data in weather_data.items():
        if "times" in data and data["times"]:
            hours = [t.split("T")[1][:5] for t in data["times"]]
            break
    
    if not hours:
        plt.close()
        return None
    
    x = np.arange(len(hours))
    
    colors = {
        'ecmwf_ifs': '#e74c3c',
        'icon_eu': '#3498db',
        'meteofrance_seamless': '#2ecc71',
        'gfs_seamless': '#f39c12'
    }
    
    # Panel 1: Wind Speed
    ax1 = axes[0]
    ax1.set_facecolor('#16213e')
    
    for model_id, data in weather_data.items():
        if "wind_speed_knots" in data and data["wind_speed_knots"]:
            wind = data["wind_speed_knots"][:len(hours)]
            color = colors.get(model_id, '#ffffff')
            label = get_model_display_name(model_id)
            ax1.plot(x[:len(wind)], wind, 'o-', color=color, linewidth=2, markersize=6, label=label)
            
            if "wind_gusts_knots" in data and data["wind_gusts_knots"]:
                gusts = data["wind_gusts_knots"][:len(hours)]
                ax1.plot(x[:len(gusts)], gusts, '--', color=color, alpha=0.5, linewidth=1)
    
    ax1.set_ylabel('Ruzgar (knot)', fontsize=11, fontweight='bold')
    ax1.set_title(f'Hava Durumu Tahmini - {target_date}', fontsize=14, fontweight='bold', pad=10)
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(-0.5, len(hours)-0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels([])
    ax1.axhline(y=15, color='yellow', linestyle=':', alpha=0.5, linewidth=1)
    ax1.axhline(y=20, color='orange', linestyle=':', alpha=0.5, linewidth=1)
    ax1.axhline(y=25, color='red', linestyle=':', alpha=0.5, linewidth=1)
    
    # Panel 2: Wind Direction
    ax2 = axes[1]
    ax2.set_facecolor('#16213e')
    
    for model_id, data in weather_data.items():
        if "wind_direction_deg" in data and data["wind_direction_deg"]:
            dirs = data["wind_direction_deg"][:len(hours)]
            color = colors.get(model_id, '#ffffff')
            ax2.scatter(x[:len(dirs)], dirs, color=color, s=40, alpha=0.8)
    
    ax2.set_ylabel('Yon (derece)', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 360)
    ax2.set_yticks([0, 90, 180, 270, 360])
    ax2.set_yticklabels(['K', 'D', 'G', 'B', 'K'])
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim(-0.5, len(hours)-0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels([])
    
    # Panel 3: Wave Height
    ax3 = axes[2]
    ax3.set_facecolor('#16213e')
    
    if "wave_height_m" in marine_data and marine_data["wave_height_m"]:
        waves = marine_data["wave_height_m"][:len(hours)]
        ax3.bar(x[:len(waves)], waves, color='#00bcd4', alpha=0.7, label='Dalga')
        
        if "swell_wave_height_m" in marine_data and marine_data["swell_wave_height_m"]:
            swell = marine_data["swell_wave_height_m"][:len(hours)]
            ax3.plot(x[:len(swell)], swell, 'o-', color='#9c27b0', linewidth=2, label='Swell')
    
    ax3.set_ylabel('Dalga (m)', fontsize=11, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_xlim(-0.5, len(hours)-0.5)
    ax3.set_xticks(x)
    ax3.set_xticklabels([])
    
    # Panel 4: Temperature
    ax4 = axes[3]
    ax4.set_facecolor('#16213e')
    
    for model_id, data in weather_data.items():
        if "temperature_c" in data and data["temperature_c"]:
            temps = data["temperature_c"][:len(hours)]
            color = colors.get(model_id, '#ffffff')
            ax4.plot(x[:len(temps)], temps, 'o-', color=color, linewidth=2, markersize=4)
    
    ax4.set_ylabel('Sicaklik (C)', fontsize=11, fontweight='bold')
    ax4.set_xlabel('Saat', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_xlim(-0.5, len(hours)-0.5)
    ax4.set_xticks(x)
    ax4.set_xticklabels(hours, rotation=45, ha='right')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, facecolor='#1a1a2e', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    chart_bytes = buf.getvalue()
    plt.close()
    
    return chart_bytes


def get_model_display_name(model_id: str) -> str:
    """Get display name for model"""
    names = {
        'ecmwf_ifs': 'ECMWF IFS',
        'icon_eu': 'ICON-EU',
        'meteofrance_seamless': 'Météo-France',
        'gfs_seamless': 'GFS (NOAA)'
    }
    return names.get(model_id, model_id)


def get_short_model_name(model_id: str) -> str:
    """Get short model name for legend"""
    names = {
        'ecmwf_ifs': 'ECMWF',
        'icon_eu': 'ICON-EU',
        'meteofrance_seamless': 'MeteoFR',
        'gfs_seamless': 'GFS'
    }
    return names.get(model_id, model_id)


def chart_to_base64(chart_bytes: bytes) -> str:
    """Convert chart bytes to base64 string"""
    if chart_bytes is None:
        return None
    return base64.b64encode(chart_bytes).decode('utf-8')


def create_station_infographic(station_data: Dict[str, Any], location: Dict[str, Any]) -> bytes:
    """
    Create an infographic showing current station measurements
    
    Args:
        station_data: Station data with measurements
        location: Location info with lat/lon
    
    Returns:
        PNG image as bytes
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    if not station_data.get("available"):
        return None
    
    measurements = station_data.get("measurements", {})
    if not measurements:
        return None
    
    # Create figure
    fig = plt.figure(figsize=(10, 6))
    fig.patch.set_facecolor('#1a1a2e')
    
    # Main title
    station_name = station_data.get("station_name", "İstasyon")
    obs_time = station_data.get("observation_time", "")
    if obs_time:
        try:
            dt = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
            obs_time_str = dt.strftime("%H:%M UTC")
        except:
            obs_time_str = obs_time
    else:
        obs_time_str = ""
    
    fig.suptitle(f'ANLIK HAVA DURUMU', fontsize=18, fontweight='bold', color='white', y=0.98)
    fig.text(0.5, 0.92, f'{station_name} | {obs_time_str}', fontsize=12, ha='center', color='#BDC3C7')
    
    # Create grid for cards
    gs = fig.add_gridspec(2, 4, hspace=0.3, wspace=0.3, left=0.05, right=0.95, top=0.85, bottom=0.15)
    
    # Card 1: Temperature
    ax1 = fig.add_subplot(gs[0, 0])
    _draw_metric_card(ax1, 'SICAKLIK', 
                     f"{measurements.get('temperature_c', '--')}°C",
                     '#FF5722', '#FBE9E7')
    
    # Card 2: Wind Speed
    ax2 = fig.add_subplot(gs[0, 1])
    wind = measurements.get('wind_knots', '--')
    wind_color = get_wind_color(wind) if isinstance(wind, (int, float)) else '#E3F2FD'
    _draw_metric_card(ax2, 'RUZGAR', 
                     f"{wind} knot",
                     '#2196F3', wind_color)
    
    # Card 3: Wind Direction with compass
    ax3 = fig.add_subplot(gs[0, 2])
    wind_dir = measurements.get('wind_direction', '--')
    if isinstance(wind_dir, (int, float)):
        arrow = get_direction_arrow(wind_dir)
        dir_text = f"{arrow} {wind_dir}°"
    else:
        dir_text = str(wind_dir)
    _draw_metric_card(ax3, 'YON', dir_text, '#9C27B0', '#F3E5F5')
    
    # Card 4: Gust
    ax4 = fig.add_subplot(gs[0, 3])
    gust = measurements.get('gust_knots', '--')
    gust_color = get_wind_color(gust) if isinstance(gust, (int, float)) else '#FFEBEE'
    _draw_metric_card(ax4, 'HAMLE', 
                     f"{gust} knot" if gust != '--' else "Yok",
                     '#E91E63', gust_color if gust != '--' else '#FAFAFA')
    
    # Card 5: Pressure
    ax5 = fig.add_subplot(gs[1, 0])
    pressure = measurements.get('pressure_hpa', '--')
    _draw_metric_card(ax5, 'BASINC', 
                     f"{pressure} hPa",
                     '#00BCD4', '#E0F7FA')
    
    # Card 6: Visibility
    ax6 = fig.add_subplot(gs[1, 1])
    vis = measurements.get('visibility_km', '--')
    _draw_metric_card(ax6, 'GORUS', 
                     f"{vis} km",
                     '#4CAF50', '#E8F5E9')
    
    # Card 7: Dewpoint
    ax7 = fig.add_subplot(gs[1, 2])
    dewpoint = measurements.get('dewpoint_c', '--')
    _draw_metric_card(ax7, 'CIG NOKTASI', 
                     f"{dewpoint}°C",
                     '#607D8B', '#ECEFF1')
    
    # Card 8: Location Info
    ax8 = fig.add_subplot(gs[1, 3])
    icao = station_data.get('station_icao', 'LTFE')
    wmo = station_data.get('station_wmo', '17290')
    _draw_metric_card(ax8, 'ISTASYON', 
                     f"ICAO: {icao}\nWMO: {wmo}",
                     '#795548', '#EFEBE9', small_text=True)
    
    # Footer with location
    lat = location.get('lat', 36.97)
    lon = location.get('lon', 27.46)
    fig.text(0.5, 0.03, f'Konum: {location.get("name", "Bodrum")} | Koordinat: {lat:.3f}°K, {lon:.3f}°D', 
             fontsize=10, ha='center', color='#95A5A6')
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, facecolor='#1a1a2e', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    infographic_bytes = buf.getvalue()
    plt.close()
    
    return infographic_bytes


def _draw_metric_card(ax, title: str, value: str, accent_color: str, bg_color: str, small_text: bool = False):
    """Draw a metric card with title and value"""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Background card
    card = plt.Rectangle((0.02, 0.02), 0.96, 0.96, facecolor=bg_color, 
                         edgecolor=accent_color, linewidth=3, 
                         transform=ax.transAxes, zorder=1)
    ax.add_patch(card)
    
    # Title bar
    title_bar = plt.Rectangle((0.02, 0.75), 0.96, 0.23, facecolor=accent_color,
                              transform=ax.transAxes, zorder=2)
    ax.add_patch(title_bar)
    
    # Title text
    ax.text(0.5, 0.87, title, fontsize=10, fontweight='bold', 
           ha='center', va='center', color='white', transform=ax.transAxes, zorder=3)
    
    # Value text
    fontsize = 11 if small_text else 18
    ax.text(0.5, 0.4, value, fontsize=fontsize, fontweight='bold', 
           ha='center', va='center', color='#2C3E50', transform=ax.transAxes, zorder=3)

