#!/usr/bin/env python3
"""
PurpleAir Historical AQI Animation Generator

This script fetches actual historical data for all sensors in a region
and creates an hour-by-hour animation showing AQI changes over a week.

WARNING: This uses more API points as it queries historical data for each sensor.
For 50 sensors over 7 days (168 hours), you'll use ~50 API calls.

Usage:
    export PURPLEAIR_API_KEY="your-key-here"
    python purpleair_historical_animation.py --days 7 --hours-interval 1
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter
from PIL import Image
import json
import time


# AQI calculation (US EPA standard for PM2.5)
AQI_BREAKPOINTS = [
    (0.0, 12.0, 0, 50, "Good", "#00E400"),
    (12.1, 35.4, 51, 100, "Moderate", "#FFFF00"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "#FF7E00"),
    (55.5, 150.4, 151, 200, "Unhealthy", "#FF0000"),
    (150.5, 250.4, 201, 300, "Very Unhealthy", "#8F3F97"),
    (250.5, 500.4, 301, 500, "Hazardous", "#7E0023"),
]


def calculate_aqi(pm25):
    """Calculate AQI from PM2.5 concentration."""
    if pd.isna(pm25) or pm25 < 0:
        return None, None, "#CCCCCC"
    
    for pm_low, pm_high, aqi_low, aqi_high, category, color in AQI_BREAKPOINTS:
        if pm_low <= pm25 <= pm_high:
            aqi = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low
            return round(aqi), category, color
    
    return 500, "Hazardous", "#7E0023"


def get_sensors_in_bbox(api_key, nwlat, nwlng, selat, selng):
    """Get all outdoor sensors in a bounding box."""
    headers = {"X-API-Key": api_key}
    params = {
        "fields": "name,latitude,longitude,altitude,last_seen",
        "location_type": 0,  # Outdoor sensors
        "nwlat": nwlat,
        "nwlng": nwlng,
        "selat": selat,
        "selng": selng,
    }
    
    response = requests.get(
        "https://api.purpleair.com/v1/sensors",
        headers=headers,
        params=params
    )
    
    if response.status_code != 200:
        print(f"Error fetching sensors: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    
    if "data" in data and data["data"]:
        # sensor_index is always the first field
        sensors = []
        for row in data["data"]:
            sensor = {
                'sensor_index': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'altitude': row[4],
                'last_seen': row[5]
            }
            sensors.append(sensor)
        return pd.DataFrame(sensors)
    
    return None


def get_sensor_history(api_key, sensor_index, start_time, end_time, average=60):
    """
    Fetch historical PM2.5 data for a sensor.
    
    Args:
        average: 0 (real-time), 10, 30, or 60 (minutes)
    """
    headers = {"X-API-Key": api_key}
    params = {
        "start_timestamp": int(start_time.timestamp()),
        "end_timestamp": int(end_time.timestamp()),
        "average": average,
        "fields": "pm2.5_atm,pm2.5_cf_1"  # Use ATM for outdoor
    }
    
    try:
        response = requests.get(
            f"https://api.purpleair.com/v1/sensors/{sensor_index}/history",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and data["data"]:
                records = []
                for row in data["data"]:
                    records.append({
                        'timestamp': datetime.fromtimestamp(row[0]),
                        'pm2.5_atm': row[1],
                        'pm2.5_cf_1': row[2]
                    })
                return pd.DataFrame(records)
            else:
                return pd.DataFrame()  # Empty
        else:
            print(f"  Warning: Sensor {sensor_index} returned {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"  Error fetching sensor {sensor_index}: {e}")
        return pd.DataFrame()


def create_hourly_frames(sensors_df, historical_data, output_dir, bbox, hours_interval=1, dpi=100):
    """
    Create visualization frames for each hour.
    
    Args:
        sensors_df: DataFrame with sensor metadata
        historical_data: Dict mapping sensor_index to historical DataFrame
        output_dir: Output directory for frames
        bbox: Bounding box tuple
        hours_interval: Hours between frames (1 = every hour)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Find time range
    all_timestamps = []
    for hist in historical_data.values():
        if len(hist) > 0:
            all_timestamps.extend(hist['timestamp'].tolist())
    
    if not all_timestamps:
        print("No historical data available!")
        return []
    
    min_time = min(all_timestamps)
    max_time = max(all_timestamps)
    
    print(f"Creating frames from {min_time} to {max_time}")
    print(f"Using {hours_interval}-hour intervals")
    
    # Generate hourly timestamps
    current_time = min_time.replace(minute=0, second=0, microsecond=0)
    frame_times = []
    
    while current_time <= max_time:
        frame_times.append(current_time)
        current_time += timedelta(hours=hours_interval)
    
    print(f"Will create {len(frame_times)} frames")
    
    frame_paths = []
    
    for frame_num, target_time in enumerate(frame_times):
        # Get PM2.5 values for all sensors at this time
        sensor_data = []
        
        for _, sensor in sensors_df.iterrows():
            sensor_idx = sensor['sensor_index']
            
            if sensor_idx in historical_data:
                hist = historical_data[sensor_idx]
                
                # Find closest timestamp (within 30 minutes)
                time_diffs = abs((hist['timestamp'] - target_time).dt.total_seconds())
                
                if len(time_diffs) > 0 and time_diffs.min() < 1800:  # Within 30 minutes
                    closest_idx = time_diffs.idxmin()
                    pm25 = hist.loc[closest_idx, 'pm2.5_atm']
                    
                    aqi, category, color = calculate_aqi(pm25)
                    
                    sensor_data.append({
                        'name': sensor['name'],
                        'latitude': sensor['latitude'],
                        'longitude': sensor['longitude'],
                        'pm2.5': pm25,
                        'aqi': aqi,
                        'category': category,
                        'color': color
                    })
        
        if not sensor_data:
            continue
        
        frame_df = pd.DataFrame(sensor_data)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(14, 11))
        
        # Plot sensors with AQI colors
        for _, row in frame_df.iterrows():
            ax.scatter(
                row['longitude'],
                row['latitude'],
                c=row['color'],
                s=300,
                alpha=0.7,
                edgecolors='black',
                linewidths=2,
                zorder=5
            )
            
            # Add AQI text
            if pd.notna(row['aqi']):
                ax.text(
                    row['longitude'],
                    row['latitude'],
                    f"{int(row['aqi'])}",
                    fontsize=9,
                    ha='center',
                    va='center',
                    fontweight='bold',
                    color='black',
                    zorder=6
                )
        
        # Set bounds
        nwlat, nwlng, selat, selng = bbox
        margin = 0.02
        ax.set_xlim(nwlng - margin, selng + margin)
        ax.set_ylim(selat - margin, nwlat + margin)
        
        ax.set_xlabel('Longitude', fontsize=13)
        ax.set_ylabel('Latitude', fontsize=13)
        
        # Title with timestamp
        time_str = target_time.strftime("%A, %B %d, %Y - %H:%M")
        ax.set_title(f'Air Quality Index (AQI) - Vancouver/Surrey Region\n{time_str}',
                    fontsize=15, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Legend
        legend_elements = [
            mpatches.Patch(color='#00E400', label='Good (0-50)'),
            mpatches.Patch(color='#FFFF00', label='Moderate (51-100)'),
            mpatches.Patch(color='#FF7E00', label='Unhealthy for Sensitive (101-150)'),
            mpatches.Patch(color='#FF0000', label='Unhealthy (151-200)'),
            mpatches.Patch(color='#8F3F97', label='Very Unhealthy (201-300)'),
            mpatches.Patch(color='#7E0023', label='Hazardous (301+)'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.9)
        
        # Statistics box
        valid_aqi = frame_df['aqi'].dropna()
        if len(valid_aqi) > 0:
            stats = (
                f"Sensors: {len(valid_aqi)} | "
                f"Average AQI: {valid_aqi.mean():.1f} | "
                f"Min: {valid_aqi.min():.0f} | "
                f"Max: {valid_aqi.max():.0f}"
            )
            ax.text(
                0.99, 0.01, stats,
                transform=ax.transAxes,
                fontsize=11,
                ha='right',
                va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.9)
            )
        
        plt.tight_layout()
        
        frame_path = os.path.join(output_dir, f"frame_{frame_num:04d}.png")
        plt.savefig(frame_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)  # Explicitly close the figure
        plt.clf()  # Clear the current figure
        plt.cla()  # Clear the current axes
        
        frame_paths.append(frame_path)
        
        if (frame_num + 1) % 10 == 0:
            print(f"  Created {frame_num + 1}/{len(frame_times)} frames")
            # Force garbage collection periodically
            import gc
            gc.collect()
    
    print(f"Completed all {len(frame_paths)} frames")
    return frame_paths


def create_animation(frame_paths, output_path, fps=4):
    """Create GIF animation from frames (memory-efficient for large sets)."""
    print(f"\nCreating animation: {output_path}")
    
    # For large frame sets, skip GIF creation (too memory intensive)
    if len(frame_paths) > 100:
        print(f"⚠ Large animation ({len(frame_paths)} frames)")
        print(f"  Skipping GIF creation to avoid memory issues.")
        print(f"\nCreate animation with external tools:")
        print(f"  ffmpeg -framerate {fps} -pattern_type glob -i 'purpleair_frames/frame_*.png' \\")
        print(f"         -c:v libx264 -pix_fmt yuv420p aqi_animation.mp4")
        print(f"\n  Or for GIF:")
        print(f"  ffmpeg -framerate {fps} -pattern_type glob -i 'purpleair_frames/frame_*.png' \\")
        print(f"         -vf 'scale=800:-1' aqi_animation.gif")
        return
    
    # For smaller sets, create GIF in batches
    print(f"Loading {len(frame_paths)} frames...")
    images = []
    
    for i, path in enumerate(frame_paths):
        if i % 20 == 0:
            print(f"  Loading frame {i+1}/{len(frame_paths)}...")
        img = Image.open(path)
        # Reduce size if needed
        if img.size[0] > 1000:
            img = img.resize((1000, int(1000 * img.size[1] / img.size[0])), Image.Resampling.LANCZOS)
        images.append(img)
    
    print("Saving GIF...")
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=int(1000/fps),  # milliseconds per frame
        loop=0
    )
    
    print(f"Animation saved! ({len(images)} frames, {fps} fps)")


def main():
    parser = argparse.ArgumentParser(description='Create PurpleAir AQI animation')
    parser.add_argument('--days', type=int, default=7, help='Number of days of history (default: 7)')
    parser.add_argument('--hours-interval', type=int, default=1, help='Hours between frames (default: 1)')
    parser.add_argument('--fps', type=int, default=4, help='Frames per second in output (default: 4)')
    parser.add_argument('--dpi', type=int, default=100, help='Image DPI/resolution (default: 100, lower=less memory)')
    parser.add_argument('--skip-gif', action='store_true', help='Skip GIF creation (just make frames)')
    args = parser.parse_args()
    
    api_key = os.environ.get('PURPLEAIR_API_KEY')
    if not api_key:
        print("Error: Set PURPLEAIR_API_KEY environment variable")
        print("Get your key from: https://develop.purpleair.com/")
        sys.exit(1)
    
    # Vancouver/Surrey bounding box
    # BBOX = (49.35, -123.25, 49.00, -122.75)
    # Golden'ish bounding box
    # NW corner: (51.3061, -116.97414)
    # SE corner: (51.0, -116.0)
    BBOX = (51.3, -117.0, 51.0, -116.0)
    
    print("=" * 80)
    print("PurpleAir Historical AQI Animation Generator")
    print("=" * 80)
    print(f"\nConfiguration:")
#    print(f"  Region: Vancouver/Surrey, BC")
    print(f"  Region: Golden, BC")
    print(f"  Bounding box: NW({BBOX[0]}, {BBOX[1]}) to SE({BBOX[2]}, {BBOX[3]})")
    print(f"  History: {args.days} days")
    print(f"  Frame interval: {args.hours_interval} hour(s)")
    print(f"  Image DPI: {args.dpi} (lower = less memory)")
    print(f"  Skip GIF: {args.skip_gif}")
    print()
    
    # Time range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=args.days)
    
    print(f"Fetching sensors...")
    sensors_df = get_sensors_in_bbox(api_key, BBOX[0], BBOX[1], BBOX[2], BBOX[3])
    
    if sensors_df is None or len(sensors_df) == 0:
        print("No sensors found in the region!")
        sys.exit(1)
    
    print(f"Found {len(sensors_df)} sensors")
    print()
    
    # Fetch historical data for each sensor
    print(f"Fetching historical data ({start_time} to {end_time})...")
    print("This may take several minutes...")
    
    historical_data = {}
    
    for idx, (_, sensor) in enumerate(sensors_df.iterrows()):
        sensor_idx = sensor['sensor_index']
        print(f"  [{idx+1}/{len(sensors_df)}] Fetching sensor {sensor_idx} ({sensor['name']})...")
        
        hist = get_sensor_history(api_key, sensor_idx, start_time, end_time, average=60)
        
        if len(hist) > 0:
            historical_data[sensor_idx] = hist
            print(f"    Got {len(hist)} data points")
        else:
            print(f"    No data available")
        
        # Rate limiting - be nice to the API
        time.sleep(0.5)
        
        # Clean up memory every 10 sensors
        if (idx + 1) % 10 == 0:
            import gc
            gc.collect()
    
    print()
    print(f"Successfully retrieved data for {len(historical_data)}/{len(sensors_df)} sensors")
    print()
    
    # Create frames
    DIR = "/tmp"
    output_dir = DIR + "/purpleair_frames"
    frame_paths = create_hourly_frames(
        sensors_df,
        historical_data,
        output_dir,
        BBOX,
        args.hours_interval,
        args.dpi
    )
    
    if not frame_paths:
        print("No frames created!")
        sys.exit(1)
    
    # Create animation (unless skipped)
    if not args.skip_gif:
        animation_path = DIR + "/purpleair_aqi_animation.gif"
        create_animation(frame_paths, animation_path, fps=args.fps)
    else:
        print("\nSkipped GIF creation (--skip-gif flag)")
        print(f"Frames saved to: {output_dir}")
        print("\nCreate animation manually with:")
        print(f"  ffmpeg -framerate {args.fps} -pattern_type glob -i '{output_dir}/frame_*.png' \\")
        print(f"         -c:v libx264 -pix_fmt yuv420p aqi_animation.mp4")
    
    # Save data summary
    summary_path =  DIR + "/outputs/data_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(f"PurpleAir AQI Animation Data Summary\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Time period: {start_time} to {end_time}\n")
        f.write(f"Region: {BBOX}\n")
        f.write(f"Total sensors: {len(sensors_df)}\n")
        f.write(f"Sensors with data: {len(historical_data)}\n")
        f.write(f"Total frames: {len(frame_paths)}\n")
        f.write(f"\nSensors:\n")
        for _, sensor in sensors_df.iterrows():
            data_points = len(historical_data.get(sensor['sensor_index'], []))
            f.write(f"  {sensor['sensor_index']}: {sensor['name']} ({data_points} points)\n")
    
    print(f"\nSummary saved to: {summary_path}")
    print()
    print("=" * 80)
    print("Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
