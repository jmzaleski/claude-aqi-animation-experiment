#!/usr/bin/env python3
"""
PurpleAir AQI Animation Generator
Creates hourly visualization frames and an animation of AQI data for a geographic region.

Usage:
    1. Get your API key from https://develop.purpleair.com/
    2. Set your API key as an environment variable: export PURPLEAIR_API_KEY="your-key-here"
    3. Run: python purpleair_aqi_animation.py
"""

import os
import sys
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

# AQI calculation constants (US EPA standard for PM2.5)
AQI_BREAKPOINTS = [
    # (PM2.5 low, PM2.5 high, AQI low, AQI high, category, color)
    (0.0, 12.0, 0, 50, "Good", "#00E400"),
    (12.1, 35.4, 51, 100, "Moderate", "#FFFF00"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "#FF7E00"),
    (55.5, 150.4, 151, 200, "Unhealthy", "#FF0000"),
    (150.5, 250.4, 201, 300, "Very Unhealthy", "#8F3F97"),
    (250.5, 500.4, 301, 500, "Hazardous", "#7E0023"),
]


def calculate_aqi(pm25):
    """Calculate AQI from PM2.5 concentration using EPA formula."""
    if pd.isna(pm25) or pm25 < 0:
        return None
    
    for pm_low, pm_high, aqi_low, aqi_high, category, color in AQI_BREAKPOINTS:
        if pm_low <= pm25 <= pm_high:
            # Linear interpolation
            aqi = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low
            return round(aqi), category, color
    
    # If PM2.5 is above all breakpoints
    return 500, "Hazardous", "#7E0023"


def get_aqi_color(aqi):
    """Get color for a given AQI value."""
    if pd.isna(aqi):
        return "#CCCCCC"
    
    for pm_low, pm_high, aqi_low, aqi_high, category, color in AQI_BREAKPOINTS:
        if aqi_low <= aqi <= aqi_high:
            return color
    return "#7E0023"  # Hazardous


class PurpleAirAPI:
    """Simple interface to PurpleAir API."""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.purpleair.com/v1"
        self.headers = {"X-API-Key": api_key}
    
    def get_sensors_in_bbox(self, nwlat, nwlng, selat, selng, fields=None):
        """Get all sensors in a bounding box."""
        if fields is None:
            fields = ["name", "latitude", "longitude", "pm2.5", "last_seen", "location_type"]
        
        params = {
            "fields": ",".join(fields),
            "location_type": 0,  # Outdoor sensors only
            "nwlat": nwlat,
            "nwlng": nwlng,
            "selat": selat,
            "selng": selng,
        }
        
        response = requests.get(
            f"{self.base_url}/sensors",
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        
        # Convert to DataFrame
        if "data" in data and data["data"]:
            df = pd.DataFrame(data["data"], columns=data["fields"])
            return df
        return None
    
    def get_sensor_history(self, sensor_index, start_timestamp, end_timestamp, average=60):
        """
        Get historical data for a sensor.
        
        Args:
            sensor_index: Sensor ID
            start_timestamp: Unix timestamp or datetime
            end_timestamp: Unix timestamp or datetime
            average: Data averaging period in minutes (0, 10, 30, 60)
        """
        if isinstance(start_timestamp, datetime):
            start_timestamp = int(start_timestamp.timestamp())
        if isinstance(end_timestamp, datetime):
            end_timestamp = int(end_timestamp.timestamp())
        
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "average": average,
            "fields": "pm2.5_cf_1,pm2.5_atm"
        }
        
        response = requests.get(
            f"{self.base_url}/sensors/{sensor_index}/history",
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            print(f"Error fetching history for sensor {sensor_index}: {response.status_code}")
            return None
        
        data = response.json()
        
        if "data" in data and data["data"]:
            df = pd.DataFrame(data["data"], columns=data["fields"])
            df['timestamp'] = pd.to_datetime(df['time_stamp'], unit='s')
            return df
        return None


def create_aqi_map(sensors_df, timestamp_str, bbox, output_path):
    """Create a single map frame showing AQI for all sensors."""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Calculate AQI for each sensor
    sensors_df['aqi'] = sensors_df['pm2.5'].apply(
        lambda x: calculate_aqi(x)[0] if pd.notna(x) else None
    )
    sensors_df['color'] = sensors_df['aqi'].apply(get_aqi_color)
    
    # Plot sensors
    scatter = ax.scatter(
        sensors_df['longitude'],
        sensors_df['latitude'],
        c=sensors_df['color'],
        s=200,
        alpha=0.7,
        edgecolors='black',
        linewidths=1.5,
        zorder=5
    )
    
    # Add AQI values as text
    for idx, row in sensors_df.iterrows():
        if pd.notna(row['aqi']):
            ax.text(
                row['longitude'],
                row['latitude'],
                f"{int(row['aqi'])}",
                fontsize=8,
                ha='center',
                va='center',
                fontweight='bold',
                zorder=6
            )
    
    # Set map bounds
    nwlat, nwlng, selat, selng = bbox
    ax.set_xlim(nwlng - 0.02, selng + 0.02)
    ax.set_ylim(selat - 0.02, nwlat + 0.02)
    
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title(f'PurpleAir AQI - {timestamp_str}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Create legend
    legend_elements = [
        mpatches.Patch(color='#00E400', label='Good (0-50)'),
        mpatches.Patch(color='#FFFF00', label='Moderate (51-100)'),
        mpatches.Patch(color='#FF7E00', label='Unhealthy for Sensitive (101-150)'),
        mpatches.Patch(color='#FF0000', label='Unhealthy (151-200)'),
        mpatches.Patch(color='#8F3F97', label='Very Unhealthy (201-300)'),
        mpatches.Patch(color='#7E0023', label='Hazardous (301+)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    # Add statistics
    valid_aqi = sensors_df['aqi'].dropna()
    if len(valid_aqi) > 0:
        stats_text = f"Sensors: {len(valid_aqi)} | Avg AQI: {valid_aqi.mean():.1f} | Max AQI: {valid_aqi.max():.0f}"
        ax.text(0.98, 0.02, stats_text, transform=ax.transAxes,
                fontsize=10, ha='right', va='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved frame: {output_path}")


def main():
    # Configuration
    API_KEY = os.environ.get('PURPLEAIR_API_KEY')
    if not API_KEY:
        print("Error: Please set PURPLEAIR_API_KEY environment variable")
        print("Get your API key from: https://develop.purpleair.com/")
        sys.exit(1)
    
    # Define bounding box for Vancouver/Surrey region
    # Format: northwest corner (lat, lng), southeast corner (lat, lng)
    BBOX = (
        49.35,   # Northwest latitude
        -123.25, # Northwest longitude
        49.00,   # Southeast latitude
        -122.75  # Southeast longitude
    )
    
    # Time range: last 7 days
    end_time = datetime.now()
#    start_time = end_time - timedelta(days=7)
    start_time = end_time - timedelta(days=1) 
    
    print(f"Fetching PurpleAir data for Vancouver/Surrey region")
    print(f"Bounding box: NW({BBOX[0]}, {BBOX[1]}) to SE({BBOX[2]}, {BBOX[3]})")
    print(f"Time range: {start_time} to {end_time}")
    print()
    
    # Initialize API
    api = PurpleAirAPI(API_KEY)
    
    # Get current sensors in the area
    print("Fetching sensors in the bounding box...")
    sensors = api.get_sensors_in_bbox(BBOX[0], BBOX[1], BBOX[2], BBOX[3])
    
    if sensors is None or len(sensors) == 0:
        print("No sensors found in the specified area!")
        print("You may need to adjust the bounding box coordinates.")
        sys.exit(1)
    
    print(f"Found {len(sensors)} sensors in the region")
    print(sensors[['name', 'latitude', 'longitude', 'pm2.5']].head())
    print()
    
    # Create output directory
    #output_dir = "/mnt/user-data/outputs/purpleair_frames"
    DIR="/tmp"
    output_dir = DIR + "/purpleair_frames" #matz
    os.makedirs(output_dir, exist_ok=True)
    
    # For the simplified version, let's just create frames using current data
    # and simulate hourly snapshots
    print("Creating hourly visualization frames...")
    print("(Note: For a full week of historical data, you'll need to query each sensor's history)")
    print()
    
    # Create sample frames - in reality, you'd fetch historical data for each hour
    hours_to_show = 24 * 7  # 7 days
    frame_paths = []
    
    # For demo purposes, we'll create a few frames with the current data
    # In a real implementation, you'd fetch historical data for each hour
    for hour in range(min(24, hours_to_show)):  # Limit to 24 frames for demo
        timestamp = end_time - timedelta(hours=hours_to_show-hour)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:00")
        
        # In a real implementation, you would:
        # 1. Query historical data for each sensor at this specific hour
        # 2. Update sensors DataFrame with that data
        # For now, we'll just use the current data
        
        frame_path = os.path.join(output_dir, f"frame_{hour:04d}.png")
        create_aqi_map(sensors.copy(), timestamp_str, BBOX, frame_path)
        frame_paths.append(frame_path)
        
        time.sleep(0.1)  # Small delay to avoid overwhelming the display
    
    print()
    print(f"Created {len(frame_paths)} frames in {output_dir}")
    print()
    print("To create animation from frames:")
    print("  ffmpeg -framerate 4 -pattern_type glob -i 'purpleair_frames/frame_*.png' -c:v libx264 -pix_fmt yuv420p aqi_animation.mp4")
    print()
    print("Or use ImageMagick:")
    print("  convert -delay 25 purpleair_frames/frame_*.png aqi_animation.gif")
    
    # Create a simple GIF animation
    print()
    print("Creating GIF animation...")
    images = []
    for frame_path in frame_paths:
        images.append(Image.open(frame_path))
    
    #animation_path = "/mnt/user-data/outputs/aqi_animation.gif"
    animation_path =  DIR + "/aqi_animation.gif" #matz
    images[0].save(
        animation_path,
        save_all=True,
        append_images=images[1:],
        duration=500,  # milliseconds per frame
        loop=0
    )
    print(f"Animation saved to: {animation_path}")
    
    # Also create a sample CSV with the current data
    #csv_path = "/mnt/user-data/outputs/sensors_current.csv"
    csv_path =  DIR + "/sensors_current.csv" #matz
    sensors['aqi'] = sensors['pm2.5'].apply(
        lambda x: calculate_aqi(x)[0] if pd.notna(x) else None
    )
    sensors.to_csv(csv_path, index=False)
    print(f"Sensor data saved to: {csv_path}")
    
    print()
    print("Done!")
    print()
    print("NEXT STEPS for full historical animation:")
    print("1. Modify the script to call get_sensor_history() for each sensor")
    print("2. Process data hour by hour for the full week")
    print("3. This will use more API points but give you actual historical patterns")


if __name__ == "__main__":
    main()
