"""
Weather Visualization Module
Creates Windguru-style charts for weather data
"""
import io
import base64
from typing import Dict, Any, List
from datetime import datetime

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def create_windguru_chart(weather_data: Dict[str, Any], marine_data: Dict[str, Any], target_date: str) -> bytes:
    """
    Create a Windguru-style weather chart
    
    Args:
        weather_data: Weather data from multiple models
        marine_data: Marine/wave data
        target_date: Target date
    
    Returns:
        PNG image as bytes
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    # Set up the figure with dark theme like Windguru
    plt.style.use('dark_background')
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1.5, 1, 1]})
    fig.patch.set_facecolor('#1a1a2e')
    
    # Get hours from first valid model
    hours = []
    for model_id, data in weather_data.items():
        if "times" in data and data["times"]:
            hours = [t.split("T")[1][:5] for t in data["times"]]
            break
    
    if not hours:
        plt.close()
        return None
    
    x = np.arange(len(hours))
    
    # Color scheme
    colors = {
        'ecmwf_ifs': '#e74c3c',      # Red
        'icon_eu': '#3498db',         # Blue
        'meteofrance_seamless': '#2ecc71',  # Green
        'gfs_seamless': '#f39c12'     # Orange
    }
    
    # === Panel 1: Wind Speed ===
    ax1 = axes[0]
    ax1.set_facecolor('#16213e')
    
    for model_id, data in weather_data.items():
        if "wind_speed_knots" in data and data["wind_speed_knots"]:
            wind = data["wind_speed_knots"][:len(hours)]
            color = colors.get(model_id, '#ffffff')
            label = get_short_model_name(model_id)
            ax1.plot(x[:len(wind)], wind, 'o-', color=color, linewidth=2, markersize=6, label=label)
            
            # Add gust line as dashed
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
    
    # Add wind threshold lines
    ax1.axhline(y=15, color='yellow', linestyle=':', alpha=0.5, linewidth=1)
    ax1.axhline(y=20, color='orange', linestyle=':', alpha=0.5, linewidth=1)
    ax1.axhline(y=25, color='red', linestyle=':', alpha=0.5, linewidth=1)
    
    # === Panel 2: Wind Direction ===
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
    
    # === Panel 3: Wave Height ===
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
    
    # === Panel 4: Temperature ===
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
    
    # Adjust layout
    plt.tight_layout()
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, facecolor='#1a1a2e', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    chart_bytes = buf.getvalue()
    plt.close()
    
    return chart_bytes


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
