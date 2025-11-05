#!/usr/bin/env python3
"""
PurpleAir API Setup and Test Script

This script helps you:
1. Test your API key
2. Find sensors in your area
3. Verify data access

Before running:
    export PURPLEAIR_API_KEY="your-api-key-here"
"""

import os
import sys
import requests
from datetime import datetime


def test_api_key(api_key):
    """Test if the API key is valid."""
    print("Testing API key...")
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(
            "https://api.purpleair.com/v1/keys",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API key is valid!")
            print(f"  Key type: {data.get('api_key_type', 'N/A')}")
            if 'api_version' in data:
                print(f"  API version: {data['api_version']}")
            return True
        else:
            print(f"✗ API key test failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error testing API key: {e}")
        return False


def find_sensors_in_area(api_key, nwlat, nwlng, selat, selng):
    """Find all outdoor sensors in a bounding box."""
    print(f"\nSearching for sensors in area:")
    print(f"  NW corner: ({nwlat}, {nwlng})")
    print(f"  SE corner: ({selat}, {selng})")
    
    headers = {"X-API-Key": api_key}
    params = {
        "fields": "name,latitude,longitude,pm2.5,last_seen,altitude",
        "location_type": 0,  # Outdoor only
        "nwlat": nwlat,
        "nwlng": nwlng,
        "selat": selat,
        "selng": selng,
    }
    
    try:
        response = requests.get(
            "https://api.purpleair.com/v1/sensors",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()

            N=10
            if "data" in data and data["data"]:
                print(f"✓ Found {len(data['data'])} sensors")
                print(f"\nFirst ",N," sensors:")
                print(f"{'Name':<30} {'Lat':<10} {'Lon':<11} {'PM2.5':<8} {'Last Seen'}")
                print("-" * 85)
                
                fields = data["fields"]
                name_idx = fields.index("name")
                lat_idx = fields.index("latitude")
                lon_idx = fields.index("longitude")
                pm25_idx = fields.index("pm2.5")
                seen_idx = fields.index("last_seen")
                
                for i, sensor in enumerate(data["data"][:N]):
                    last_seen = datetime.fromtimestamp(sensor[seen_idx]).strftime("%Y-%m-%d %H:%M")
                    pm25 = f"{sensor[pm25_idx]:.1f}" if sensor[pm25_idx] is not None else "N/A"
                    print(f"{sensor[name_idx][:29]:<30} {sensor[lat_idx]:<10.5f} {sensor[lon_idx]:<11.5f} {pm25:<8} {last_seen}")
                
                return data["data"]
            else:
                print("✗ No sensors found in this area")
                return []
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def get_sensor_history_sample(api_key, sensor_index):
    """Get a small sample of historical data for a sensor."""
    print(f"\nTesting historical data access for sensor {sensor_index}...")
    
    headers = {"X-API-Key": api_key}
    
    # Get last 6 hours of data
    end_time = datetime.now()
    start_time = end_time.replace(hour=end_time.hour-6, minute=0, second=0, microsecond=0)
    
    params = {
        "start_timestamp": int(start_time.timestamp()),
        "end_timestamp": int(end_time.timestamp()),
        "average": 60,  # 1-hour averages
        "fields": "pm2.5_cf_1,pm2.5_atm"
    }
    
    try:
        response = requests.get(
            f"https://api.purpleair.com/v1/sensors/{sensor_index}/history",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and data["data"]:
                print(f"✓ Retrieved {len(data['data'])} hourly data points")
                print(f"\nSample data:")
                print(f"{'Timestamp':<20} {'PM2.5 (CF=1)':<15} {'PM2.5 (ATM)'}")
                print("-" * 55)
                
                fields = data["fields"]
                time_idx = fields.index("time_stamp")
                cf1_idx = fields.index("pm2.5_cf_1")
                atm_idx = fields.index("pm2.5_atm")
                
                for point in data["data"][:3]:
                    timestamp = datetime.fromtimestamp(point[time_idx]).strftime("%Y-%m-%d %H:%M")
                    cf1 = f"{point[cf1_idx]:.1f}" if point[cf1_idx] is not None else "N/A"
                    atm = f"{point[atm_idx]:.1f}" if point[atm_idx] is not None else "N/A"
                    print(f"{timestamp:<20} {cf1:<15} {atm}")
                
                return True
            else:
                print("✗ No historical data available")
                return False
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=" * 80)
    print("PurpleAir API Setup and Test")
    print("=" * 80)
    print()
    
    # Check for API key
    api_key = os.environ.get('PURPLEAIR_API_KEY')
    
    if not api_key:
        print("✗ No API key found!")
        print()
        print("To get started:")
        print("1. Visit: https://develop.purpleair.com/")
        print("2. Sign up with your Google account")
        print("3. Create an API key (you get 1 million free points)")
        print("4. Set the environment variable:")
        print("   export PURPLEAIR_API_KEY='your-key-here'")
        print()
        sys.exit(1)
    
    # Test the API key
    if not test_api_key(api_key):
        sys.exit(1)
    
    LATITUDE = 51.3061  # CC
    LONGITUDE = -116.97414 #CC
    DELTA = 0.5
    
    print()
    print("Choose your region:")
    #print("1. Vancouver/Surrey, BC (default)")
    print("1. Golden'ish (default) delta,long.lat=", DELTA,LATITUDE, LONGITUDE)
    print("2. Custom bounding box")
    
    choice = input("\nChoice (1/2) [1]: ").strip() or "1"


    if choice == "1":
        # Vancouver/Surrey region
        #nwlat, nwlng = 49.35, -123.25
        #selat, selng = 49.00, -122.75
        # Golden area'ish
        nwlat = (LATITUDE + DELTA)
        nwlng = (LONGITUDE - DELTA)
        selat = LATITUDE - DELTA
        selng = LONGITUDE + DELTA
        print("nwlat,nwlng=(",nwlat,nwlng,")")
        print("selat,selng=(",selat,selng,")")
    else:
        print("\nEnter bounding box coordinates:")
        nwlat = float(input("Northwest latitude: "))
        nwlng = float(input("Northwest longitude: "))
        selat = float(input("Southeast latitude: "))
        selng = float(input("Southeast longitude: "))
    
    # Find sensors
    sensors = find_sensors_in_area(api_key, nwlat, nwlng, selat, selng)
    
    if sensors and len(sensors) > 0:
        # Test historical data on first sensor
        fields = ["name", "latitude", "longitude", "pm2.5", "last_seen", "altitude"]
        # Get sensor_index - it's the first field by default
        sensor_index = sensors[0][0]  # First sensor, first field (sensor_index)
        
        get_sensor_history_sample(api_key, sensor_index)
    
    print()
    print("=" * 80)
    print("Setup complete! You're ready to run the animation script.")
    print("=" * 80)


if __name__ == "__main__":
    main()
