#!/usr/bin/env python3
"""
PurpleAir AQI Animation - Properly Designed

1. Fetch all historical data (tiny amount of data)
2. Save to CSV (reusable, no API quota waste)
3. Create PNG frames one at a time (proper cleanup)
4. Use external tool to create GIF/video

Usage:
    export PURPLEAIR_API_KEY="your-key-here"
    python3 purpleair_efficient.py --days 7
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time
import gc


# AQI calculation
AQI_BREAKPOINTS = [
    (0.0, 12.0, 0, 50, "Good", "#00E400"),
    (12.1, 35.4, 51, 100, "Moderate", "#FFFF00"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "#FF7E00"),
    (55.5, 150.4, 151, 200, "Unhealthy", "#FF0000"),
    (150.5, 250.4, 201, 300, "Very Unhealthy", "#8F3F97"),
    (250.5, 500.4, 301, 500, "Hazardous", "#7E0023"),
]


def calculate_aqi(pm25):
    if pd.isna(pm25) or pm25 < 0:
        return None, None, "#CCCCCC"
    
    for pm_low, pm_high, aqi_low, aqi_high, category, color in AQI_BREAKPOINTS:
        if pm_low <= pm25 <= pm_high:
            aqi = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low
            return round(aqi), category, color
    
    return 500, "Hazardous", "#7E0023"


def get_sensors(api_key, bbox):
    """Get sensors in bounding box."""
    headers = {"X-API-Key": api_key}
    nwlat, nwlng, selat, selng = bbox
    
    params = {
        "fields": "name,latitude,longitude",
        "location_type": 0,
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
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    
    if "data" in data and data["data"]:
        sensors = []
        for row in data["data"]:
            sensors.append({
                'sensor_index': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3]
            })
        return pd.DataFrame(sensors)
    
    return None


def fetch_historical_data(api_key, sensors_df, start_time, end_time, output_csv):
    """Fetch all historical data and save to CSV."""
    print(f"\nFetching historical data...")
    print(f"  Time range: {start_time} to {end_time}")
    print(f"  Sensors: {len(sensors_df)}")
    
    all_data = []
    
    for idx, sensor in sensors_df.iterrows():
        sensor_idx = sensor['sensor_index']
        print(f"  [{idx+1}/{len(sensors_df)}] {sensor['name']} (ID: {sensor_idx})...", end='', flush=True)
        
        headers = {"X-API-Key": api_key}
        params = {
            "start_timestamp": int(start_time.timestamp()),
            "end_timestamp": int(end_time.timestamp()),
            "average": 60,
            "fields": "pm2.5_atm"
        }
        
        try:
            response = requests.get(
                f"https://api.purpleair.com/v1/sensors/{sensor_idx}/history",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    for row in data["data"]:
                        all_data.append({
                            'sensor_index': sensor_idx,
                            'timestamp': datetime.fromtimestamp(row[0]),
                            'pm2.5': row[1]
                        })
                    print(f" {len(data['data'])} points")
                else:
                    print(" no data")
            else:
                print(f" error {response.status_code}")
        
        except Exception as e:
            print(f" failed: {e}")
        
        time.sleep(0.3)  # Rate limiting
    
    # Create DataFrame and save
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(output_csv, index=False)
        print(f"\n✓ Saved {len(df)} data points to {output_csv}")
        print(f"  File size: {os.path.getsize(output_csv) / 1024 / 1024:.2f} MB")
        return df
    
    return None


def load_data(csv_file):
    """Load historical data from CSV."""
    print(f"\nLoading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"  Loaded {len(df)} data points")
    return df


def create_single_frame(sensors_df, historical_df, target_time, bbox, output_path, dpi=100):
    """Create one PNG frame. Clean up properly."""
    
    # Get data for this time (within 30 min window)
    time_window = timedelta(minutes=30)
    mask = (historical_df['timestamp'] >= target_time - time_window) & \
           (historical_df['timestamp'] <= target_time + time_window)
    
    frame_data = historical_df[mask].copy()
    
    if len(frame_data) == 0:
        return False
    
    # Get closest reading for each sensor
    frame_data['time_diff'] = abs((frame_data['timestamp'] - target_time).dt.total_seconds())
    frame_data = frame_data.sort_values('time_diff').groupby('sensor_index').first().reset_index()
    
    # Merge with sensor locations
    frame_data = frame_data.merge(sensors_df, on='sensor_index', how='inner')
    
    # Calculate AQI
    frame_data['aqi'] = frame_data['pm2.5'].apply(lambda x: calculate_aqi(x)[0])
    frame_data['color'] = frame_data['aqi'].apply(lambda x: calculate_aqi(x)[2] if pd.notna(x) else "#CCCCCC")
    
    # Create plot
    fig = plt.figure(figsize=(14, 11))
    ax = fig.add_subplot(111)
    
    # Plot sensors
    for _, row in frame_data.iterrows():
        ax.scatter(row['longitude'], row['latitude'], 
                  c=row['color'], s=300, alpha=0.7,
                  edgecolors='black', linewidths=2, zorder=5)
        
        if pd.notna(row['aqi']):
            ax.text(row['longitude'], row['latitude'], f"{int(row['aqi'])}",
                   fontsize=9, ha='center', va='center', 
                   fontweight='bold', color='black', zorder=6)
    
    # Set bounds
    nwlat, nwlng, selat, selng = bbox
    margin = 0.02
    ax.set_xlim(nwlng - margin, selng + margin)
    ax.set_ylim(selat - margin, nwlat + margin)
    
    ax.set_xlabel('Longitude', fontsize=13)
    ax.set_ylabel('Latitude', fontsize=13)
    
    # Title
    time_str = target_time.strftime("%A, %B %d, %Y - %H:%M")
#    ax.set_title(f'Air Quality Index (AQI) - Vancouver/Surrey Region\n{time_str}',
#                fontsize=15, fontweight='bold', pad=20)
    title=f'Air Quality Index (AQI) - ' + REGION_TITLE #matz
    print("make animation with title", title)
    ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    
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
    
    # Statistics
    valid_aqi = frame_data['aqi'].dropna()
    if len(valid_aqi) > 0:
        stats = (f"Sensors: {len(valid_aqi)} | Avg: {valid_aqi.mean():.1f} | "
                f"Min: {valid_aqi.min():.0f} | Max: {valid_aqi.max():.0f}")
        ax.text(0.99, 0.01, stats, transform=ax.transAxes, fontsize=11,
               ha='right', va='bottom',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.9))
    
    # Save
    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    
    # CRITICAL: Clean up completely
    plt.close(fig)
    del fig, ax
    gc.collect()
    
    return True


def main():
    parser = argparse.ArgumentParser(description='PurpleAir AQI Animation (efficient version)')
    parser.add_argument('--days', type=int, default=1, help='Days of history')
    parser.add_argument('--hours-interval', type=int, default=1, help='Hours between frames')
    parser.add_argument('--dpi', type=int, default=100, help='Image resolution')
    parser.add_argument('--use-cached', action='store_true', help='Use existing CSV data')
    args = parser.parse_args()
    
    api_key = os.environ.get('PURPLEAIR_API_KEY')
    if not api_key and not args.use_cached:
        print("Error: Set PURPLEAIR_API_KEY or use --use-cached")
        sys.exit(1)
    
    # Output directory configuration
    DIR = "/tmp/purple-air"
    # Vancouver/Surrey bounding box
    # BBOX = (49.35, -123.25, 49.00, -122.75)
    # REGION_TITLE = f'vancouver\n{time_str}'

    # Golden'ish bounding box
    # NW corner: (51.3061, -116.97414)
    # SE corner: (51.0, -116.0)
    BBOX = (51.5, -117.5, 51.0, -116.0)
    REGION_TITLE = f'Golden Region\n{time_str}'
    
    print("=" * 80)
    print("PurpleAir AQI Animation - Efficient Version")
    print("=" * 80)
    
    # Create output directories
    os.makedirs(DIR, exist_ok=True)
    frames_dir = os.path.join(DIR, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    csv_file = os.path.join(DIR, "purpleair_data.csv")
    sensors_csv = os.path.join(DIR, "purpleair_sensors.csv")
    
    # Step 1: Get or load sensor list
    if args.use_cached and os.path.exists(sensors_csv):
        print(f"\nUsing cached sensors from {sensors_csv}")
        sensors_df = pd.read_csv(sensors_csv)
    else:
        print("\nFetching sensors...")
        sensors_df = get_sensors(api_key, BBOX)
        if sensors_df is None or len(sensors_df) == 0:
            print("No sensors found!")
            sys.exit(1)
        sensors_df.to_csv(sensors_csv, index=False)
        print(f"✓ Found {len(sensors_df)} sensors, saved to {sensors_csv}")
    
    # Step 2: Fetch or load historical data
    #end_time = datetime.now()
    #start_time = end_time - timedelta(days=args.days)

    # scott times
    start_time = datetime.strptime("2025-10-29","%Y-%m-%d")
    end_time = start_time + timedelta(2)
    print("times hacked for scott, override commandline options, start_time=",start_time," end_time=", end_time)
    
    if args.use_cached and os.path.exists(csv_file):
        print(f"\nUsing cached data from {csv_file}")
        historical_df = load_data(csv_file)
    else:
        historical_df = fetch_historical_data(api_key, sensors_df, start_time, end_time, csv_file)
        if historical_df is None or len(historical_df) == 0:
            print("No historical data retrieved!")
            sys.exit(1)
    
    # Step 3: Generate frame times
    current_time = start_time.replace(minute=0, second=0, microsecond=0)
    frame_times = []
    while current_time <= end_time:
        frame_times.append(current_time)
        current_time += timedelta(hours=args.hours_interval)
    
    print(f"\nCreating {len(frame_times)} frames...")
    print(f"  DPI: {args.dpi}")
    print(f"  Output: {frames_dir}")
    print()
    
    # Step 4: Create frames ONE AT A TIME
    success_count = 0
    for i, target_time in enumerate(frame_times):
        frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
        
        if create_single_frame(sensors_df, historical_df, target_time, BBOX, frame_path, args.dpi):
            success_count += 1
            print(f"  [{i+1}/{len(frame_times)}] ✓ {target_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  [{i+1}/{len(frame_times)}] ✗ {target_time.strftime('%Y-%m-%d %H:%M')} (no data)")
        
        # Cleanup every 10 frames
        if (i + 1) % 10 == 0:
            gc.collect()
    
    print()
    print("=" * 80)
    print(f"✓ Complete! Created {success_count}/{len(frame_times)} frames")
    print("=" * 80)
    print()
    print(f"Frames: {frames_dir}")
    print(f"Data: {csv_file} (reuse with --use-cached)")
    print()
    print("Create animation:")
    print(f"  bash make_animation.sh")
    print()


if __name__ == "__main__":
    main()
