# PurpleAir AQI Animation Generator

Create animated visualizations of Air Quality Index (AQI) data from PurpleAir sensors in your region.

## Overview

This toolkit helps you:
1. **Fetch real-time and historical air quality data** from PurpleAir sensors
2. **Visualize AQI patterns** across your region
3. **Create animations** showing how air quality changes over time
4. **Identify pollution sources and patterns** in your area

Perfect for analyzing wildfire smoke, traffic patterns, industrial emissions, or general air quality trends.

## What You'll Need

1. **PurpleAir API Key** (free, 1 million points)
   - Sign up at: https://develop.purpleair.com/
   - Uses your Google account
   - No credit card required

2. **Python 3** with the following packages (script will help install):
   - requests
   - pandas
   - matplotlib
   - pillow (PIL)

## Quick Start

### Step 1: Get Your API Key

```bash
# Visit https://develop.purpleair.com/
# Sign up and create an API key
# Then set it as an environment variable:

export PURPLEAIR_API_KEY="your-key-here"

# Or add to your ~/.bashrc or ~/.zshrc:
echo 'export PURPLEAIR_API_KEY="your-key-here"' >> ~/.bashrc
```

### Step 2: Test Your Setup

```bash
python test_purpleair_api.py
```

This will:
- Verify your API key works
- Show sensors in the Vancouver/Surrey region
- Test historical data access
- Give you confidence everything is configured correctly

### Step 3: Create Your Animation

**Option A: Quick Demo (current data only)**
```bash
python purpleair_aqi_animation.py
```
- Creates 24 sample frames using current sensor data
- Fast, uses minimal API points
- Good for testing visualization style

**Option B: Full Historical Animation (recommended)**
```bash
python purpleair_historical_animation.py --days 7 --hours-interval 1
```
- Fetches actual historical data for each sensor
- Creates one frame per hour for 7 days (168 frames)
- Uses ~50 API calls for 50 sensors
- Shows real air quality patterns and changes

### Step 4: View Your Results

Output files will be in `/mnt/user-data/outputs/`:
- `purpleair_aqi_animation.gif` - The animated visualization
- `purpleair_frames/` - Individual frame images (PNG)
- `data_summary.txt` - Statistics about your data
- `sensors_current.csv` - Sensor data in CSV format

## Understanding the Visualization

### AQI Color Scale
- **Green (0-50)**: Good - Air quality is satisfactory
- **Yellow (51-100)**: Moderate - Acceptable for most people
- **Orange (101-150)**: Unhealthy for Sensitive Groups
- **Red (151-200)**: Unhealthy - Everyone may experience effects
- **Purple (201-300)**: Very Unhealthy - Health alert
- **Maroon (301+)**: Hazardous - Emergency conditions

### Reading the Maps
- Each **circle** represents a PurpleAir sensor
- **Color** shows the AQI category
- **Number** inside is the actual AQI value
- **Statistics box** shows average, min, and max AQI for that hour

## Advanced Usage

### Custom Time Ranges

```bash
# Last 3 days, frame every 2 hours
python purpleair_historical_animation.py --days 3 --hours-interval 2

# Last 24 hours, frame every hour
python purpleair_historical_animation.py --days 1 --hours-interval 1

# Last 14 days, frame every 6 hours
python purpleair_historical_animation.py --days 14 --hours-interval 6
```

### Adjust Animation Speed

```bash
# Slower animation (2 frames per second)
python purpleair_historical_animation.py --days 7 --fps 2

# Faster animation (8 frames per second)
python purpleair_historical_animation.py --days 7 --fps 8
```

### Different Regions

To analyze a different area, edit the `BBOX` variable in the scripts:

```python
# Format: (NW latitude, NW longitude, SE latitude, SE longitude)
BBOX = (49.35, -123.25, 49.00, -122.75)  # Vancouver/Surrey

# Examples:
# Victoria: (48.50, -123.45, 48.40, -123.30)
# Kelowna: (49.95, -119.50, 49.80, -119.35)
# Seattle: (47.75, -122.45, 47.50, -122.25)
```

You can find coordinates using:
- Google Maps (right-click → "What's here?")
- https://www.latlong.net/
- Google Earth Pro (shows coordinates at bottom)

## API Usage and Costs

### Point System
- PurpleAir uses a point-based system
- New accounts get **1 million points free**
- Sensor owners can view their own sensor data without using points

### Typical Usage
- **Get sensors in area**: ~1 point
- **Get sensor history**: ~1 point per sensor per call
- **Full 7-day animation** (50 sensors): ~50 points

With 1 million free points, you can create **thousands** of animations!

### Rate Limiting
The scripts include automatic rate limiting to be respectful:
- 0.5 second delay between sensor queries
- Timeout handling for slow responses
- Retry logic for transient errors

## Troubleshooting

### "No sensors found"
- Check your bounding box coordinates
- Try widening the area
- Verify sensors exist in your region on https://map.purpleair.com/

### "API key invalid"
- Make sure you set the environment variable correctly
- Check for typos in your API key
- Verify the key at https://develop.purpleair.com/

### "No historical data"
- Some sensors may be offline or have gaps in data
- Try a shorter time period
- The script will skip sensors without data

### Animation looks jerky
- Increase `--fps` for smoother playback
- Decrease `--hours-interval` for more frames
- Check that sensors have consistent data

## Use Cases

### Wildfire Smoke Analysis
```bash
# Create animation during fire season
python purpleair_historical_animation.py --days 7 --hours-interval 2
# Look for patterns: When does smoke arrive? When does it clear?
```

### Traffic Pattern Detection
```bash
# Compare weekday vs weekend
python purpleair_historical_animation.py --days 7 --hours-interval 1
# Watch for morning/evening spikes near highways
```

### Industrial Source Identification
```bash
# Long-term pattern analysis
python purpleair_historical_animation.py --days 14 --hours-interval 6
# Look for consistent pollution sources
```

### Weather Event Impact
```bash
# Before/during/after analysis
python purpleair_historical_animation.py --days 3 --hours-interval 1
# See how wind, rain, or inversions affect air quality
```

## Further Enhancement Ideas

1. **Overlay wind data** to show pollution transport
2. **Add basemap** with streets/landmarks using cartopy
3. **Compare to official monitoring stations** (EPA AirNow)
4. **Generate statistics** (daily averages, exceedance counts)
5. **Create time-series plots** for individual sensors
6. **Export to video format** (MP4) using ffmpeg
7. **Add weather data** (temperature, humidity, pressure)

## Converting to Video

If you want higher quality video output:

```bash
# Install ffmpeg
sudo apt-get install ffmpeg

# Create MP4 from frames
ffmpeg -framerate 4 -pattern_type glob -i 'purpleair_frames/frame_*.png' \
       -c:v libx264 -pix_fmt yuv420p -crf 23 aqi_animation.mp4

# Higher quality (larger file)
ffmpeg -framerate 4 -pattern_type glob -i 'purpleair_frames/frame_*.png' \
       -c:v libx264 -pix_fmt yuv420p -crf 18 aqi_animation_hq.mp4
```

## Data Attribution

Per PurpleAir's requirements, if you share these visualizations publicly:

> "Air quality data provided by PurpleAir - www.purpleair.com"

## Technical Notes

### PM2.5 Fields
- `pm2.5_cf_1`: Indoor/controlled environment (CF=1)
- `pm2.5_atm`: Outdoor/atmospheric (ATM) - used in this tool
- PurpleAir displays CF=1 on their map, but EPA recommends ATM for outdoor

### AQI Calculation
Uses the official EPA formula for PM2.5 AQI:
- https://www.airnow.gov/aqi/aqi-basics/
- Linear interpolation between breakpoint ranges
- Real-time calculation, no API lookup needed

### Time Averaging
- Scripts use 60-minute averages by default
- Can be changed to 0, 10, or 30 minutes
- Hourly averages balance detail with API efficiency

## Resources

- **PurpleAir Map**: https://map.purpleair.com/
- **API Documentation**: https://api.purpleair.com/
- **Community Forum**: https://community.purpleair.com/
- **EPA AQI Info**: https://www.airnow.gov/aqi/
- **Developer Portal**: https://develop.purpleair.com/

## License

These scripts are provided as-is for educational and research purposes. 

PurpleAir data usage must comply with their terms of service and data license:
https://www2.purpleair.com/pages/terms

## Author

Created for analyzing air quality patterns in Vancouver/Surrey, BC.

Contributions and improvements welcome!
