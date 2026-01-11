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
        return '#E8F5E9'    # Very light green (almost white)
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
        return '#E3F2FD'    # Very light blue
    elif height < 0.5:
        return '#BBDEFB'    # Light blue
    elif height < 0.8:
        return '#90CAF9'    # Blue
    elif height < 1.0:
        return '#64B5F6'    # Medium blue
    elif height < 1.5:
        return '#42A5F5'    # Darker blue
    elif height < 2.0:
        return '#2196F3'    # Strong blue
    else:
        return '#1565C0'    # Dark blue


def get_temp_color(temp: float) -> str:
    """Get color for temperature"""
    if temp < 10:
        return '#90CAF9'    # Cold - blue
    elif temp < 15:
        return '#E1F5FE'    # Cool
    elif temp < 20:
        return '#FFF9C4'    # Mild - light yellow
    elif temp < 25:
        return '#FFEB3B'    # Warm - yellow
    elif temp < 30:
        return '#FF9800'    # Hot - orange
    else:
        return '#FF5722'    # Very hot - deep orange


def get_direction_arrow(degrees: float) -> str:
    """Get arrow character for wind direction"""
    arrows = ['↓', '↙', '←', '↖', '↑', '↗', '→', '↘']
    index = round(degrees / 45) % 8
    return arrows[index]


def create_windguru_table(weather_data: Dict[str, Any], marine_data: Dict[str, Any], target_date: str) -> bytes:
    """
    Create a Windguru-style colored table
    
    Args:
        weather_data: Weather data from multiple models
        marine_data: Marine/wave data
        target_date: Target date
    
    Returns:
        PNG image as bytes
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    # Get hours from first valid model
    hours = []
    first_model_data = None
    for model_id, data in weather_data.items():
        if "times" in data and data["times"]:
            hours = [t.split("T")[1][:5] for t in data["times"]]
            first_model_data = data
            break
    
    if not hours or not first_model_data:
        return None
    
    # Prepare data for table
    n_hours = len(hours)
    n_models = len([m for m, d in weather_data.items() if "times" in d])
    
    # Calculate figure size based on data
    fig_width = max(12, n_hours * 0.8)
    fig_height = 3 + n_models * 1.5
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, n_hours + 1)
    ax.set_ylim(0, 6 + n_models)
    ax.axis('off')
    fig.patch.set_facecolor('#2C3E50')
    
    # Title
    ax.text(n_hours/2 + 0.5, 5.5 + n_models, f'HAVA DURUMU TAHMİNİ - {target_date}', 
            fontsize=14, fontweight='bold', ha='center', va='center', color='white')
    ax.text(n_hours/2 + 0.5, 5 + n_models, 'Kara Ada, Bodrum', 
            fontsize=10, ha='center', va='center', color='#BDC3C7')
    
    # Column headers (hours)
    row_y = 4.5 + n_models
    ax.add_patch(plt.Rectangle((0, row_y - 0.4), n_hours + 1, 0.8, facecolor='#34495E', edgecolor='#2C3E50'))
    ax.text(0.5, row_y, 'SAAT', fontsize=8, fontweight='bold', ha='center', va='center', color='white')
    for i, hour in enumerate(hours):
        ax.text(i + 1.5, row_y, hour, fontsize=9, fontweight='bold', ha='center', va='center', color='white')
    
    current_row = 3.5 + n_models
    
    # === WIND SPEED ROWS FOR EACH MODEL ===
    for model_id, data in weather_data.items():
        if "wind_speed_knots" not in data or not data["wind_speed_knots"]:
            continue
        
        model_name = get_short_model_name(model_id)
        
        # Wind row header
        ax.add_patch(plt.Rectangle((0, current_row - 0.4), 1, 0.8, facecolor='#3498DB', edgecolor='#2C3E50'))
        ax.text(0.5, current_row, f'{model_name}\nknot', fontsize=7, fontweight='bold', 
                ha='center', va='center', color='white')
        
        # Wind values with colors
        winds = data["wind_speed_knots"][:n_hours]
        for i, wind in enumerate(winds):
            color = get_wind_color(wind)
            text_color = 'black' if wind < 35 else 'white'
            ax.add_patch(plt.Rectangle((i + 1, current_row - 0.4), 1, 0.8, 
                                       facecolor=color, edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 1.5, current_row, f'{wind:.0f}', fontsize=9, fontweight='bold',
                   ha='center', va='center', color=text_color)
        
        current_row -= 1
    
    # === GUST ROW (average of models) ===
    all_gusts = []
    for model_id, data in weather_data.items():
        if "wind_gusts_knots" in data and data["wind_gusts_knots"]:
            all_gusts.append(data["wind_gusts_knots"][:n_hours])
    
    if all_gusts:
        avg_gusts = np.mean(all_gusts, axis=0)
        ax.add_patch(plt.Rectangle((0, current_row - 0.4), 1, 0.8, facecolor='#E74C3C', edgecolor='#2C3E50'))
        ax.text(0.5, current_row, 'HAMLE\nknot', fontsize=7, fontweight='bold', 
                ha='center', va='center', color='white')
        
        for i, gust in enumerate(avg_gusts):
            color = get_wind_color(gust)
            text_color = 'black' if gust < 35 else 'white'
            ax.add_patch(plt.Rectangle((i + 1, current_row - 0.4), 1, 0.8, 
                                       facecolor=color, edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 1.5, current_row, f'{gust:.0f}', fontsize=9, fontweight='bold',
                   ha='center', va='center', color=text_color)
        current_row -= 1
    
    # === WIND DIRECTION ROW ===
    all_dirs = []
    for model_id, data in weather_data.items():
        if "wind_direction_deg" in data and data["wind_direction_deg"]:
            all_dirs.append(data["wind_direction_deg"][:n_hours])
    
    if all_dirs:
        avg_dirs = np.mean(all_dirs, axis=0)
        ax.add_patch(plt.Rectangle((0, current_row - 0.4), 1, 0.8, facecolor='#9B59B6', edgecolor='#2C3E50'))
        ax.text(0.5, current_row, 'YÖN', fontsize=7, fontweight='bold', 
                ha='center', va='center', color='white')
        
        for i, dir_deg in enumerate(avg_dirs):
            arrow = get_direction_arrow(dir_deg)
            ax.add_patch(plt.Rectangle((i + 1, current_row - 0.4), 1, 0.8, 
                                       facecolor='#ECF0F1', edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 1.5, current_row, arrow, fontsize=14, ha='center', va='center', color='#2C3E50')
        current_row -= 1
    
    # === WAVE ROW ===
    if "wave_height_m" in marine_data and marine_data["wave_height_m"]:
        waves = marine_data["wave_height_m"][:n_hours]
        ax.add_patch(plt.Rectangle((0, current_row - 0.4), 1, 0.8, facecolor='#00BCD4', edgecolor='#2C3E50'))
        ax.text(0.5, current_row, 'DALGA\nm', fontsize=7, fontweight='bold', 
                ha='center', va='center', color='white')
        
        for i, wave in enumerate(waves):
            color = get_wave_color(wave)
            ax.add_patch(plt.Rectangle((i + 1, current_row - 0.4), 1, 0.8, 
                                       facecolor=color, edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 1.5, current_row, f'{wave:.1f}', fontsize=9, fontweight='bold',
                   ha='center', va='center', color='#1565C0')
        current_row -= 1
    
    # === TEMPERATURE ROW ===
    all_temps = []
    for model_id, data in weather_data.items():
        if "temperature_c" in data and data["temperature_c"]:
            all_temps.append(data["temperature_c"][:n_hours])
    
    if all_temps:
        avg_temps = np.mean(all_temps, axis=0)
        ax.add_patch(plt.Rectangle((0, current_row - 0.4), 1, 0.8, facecolor='#FF5722', edgecolor='#2C3E50'))
        ax.text(0.5, current_row, 'SICAKLIK\n°C', fontsize=7, fontweight='bold', 
                ha='center', va='center', color='white')
        
        for i, temp in enumerate(avg_temps):
            color = get_temp_color(temp)
            ax.add_patch(plt.Rectangle((i + 1, current_row - 0.4), 1, 0.8, 
                                       facecolor=color, edgecolor='#2C3E50', linewidth=0.5))
            ax.text(i + 1.5, current_row, f'{temp:.0f}', fontsize=9, fontweight='bold',
                   ha='center', va='center', color='#333333')
        current_row -= 1
    
    # Adjust limits
    ax.set_ylim(current_row - 0.5, 6 + n_models)
    
    plt.tight_layout()
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, facecolor='#2C3E50', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    table_bytes = buf.getvalue()
    plt.close()
    
    return table_bytes


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
