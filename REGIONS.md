# Common British Columbia Region Bounding Boxes

## How to Use These

Copy the BBOX line into your script and replace the default one.

Format: `(NW_latitude, NW_longitude, SE_latitude, SE_longitude)`

## Lower Mainland / Metro Vancouver

### Vancouver/Surrey (Default)
```python
BBOX = (49.35, -123.25, 49.00, -122.75)
```
Covers: Vancouver, Burnaby, Surrey, New Westminster, Coquitlam, parts of Richmond

### Vancouver Downtown Core
```python
BBOX = (49.30, -123.20, 49.25, -123.05)
```
Covers: Downtown, West End, Kitsilano, Mount Pleasant

### Fraser Valley
```python
BBOX = (49.25, -122.90, 49.00, -121.90)
```
Covers: Langley, Abbotsford, Chilliwack, Mission

### Richmond/Delta
```python
BBOX = (49.25, -123.25, 49.05, -122.95)
```
Covers: Richmond, Delta, YVR area

### Tri-Cities (Coquitlam/Port Moody/Port Coquitlam)
```python
BBOX = (49.35, -122.95, 49.20, -122.70)
```

### North Shore (North Van/West Van)
```python
BBOX = (49.40, -123.30, 49.28, -123.00)
```

## Vancouver Island

### Greater Victoria
```python
BBOX = (48.55, -123.50, 48.40, -123.30)
```
Covers: Victoria, Saanich, Oak Bay, Esquimalt

### Nanaimo
```python
BBOX = (49.25, -124.05, 49.10, -123.90)
```

### Comox Valley
```python
BBOX = (49.75, -125.00, 49.60, -124.85)
```
Covers: Courtenay, Comox

## Interior

### Kelowna/Okanagan
```python
BBOX = (50.05, -119.65, 49.80, -119.30)
```
Covers: Kelowna, West Kelowna

### Vernon
```python
BBOX = (50.30, -119.35, 50.20, -119.20)
```

### Kamloops
```python
BBOX = (50.75, -120.40, 50.60, -120.25)
```

### Penticton
```python
BBOX = (49.55, -119.65, 49.45, -119.50)
```

## Southern Interior

### Nelson/West Kootenay
```python
BBOX = (49.55, -117.40, 49.45, -117.20)
```

### Cranbrook/East Kootenay
```python
BBOX = (49.60, -115.85, 49.45, -115.70)
```

## Northern BC

### Prince George
```python
BBOX = (53.95, -122.85, 53.85, -122.65)
```

### Fort St. John
```python
BBOX = (56.30, -120.90, 56.20, -120.75)
```

## Finding Your Own Coordinates

### Method 1: Google Maps
1. Go to https://maps.google.com
2. Right-click on the map
3. Select "What's here?"
4. Coordinates appear at the bottom

### Method 2: Google Earth Pro
1. Open Google Earth Pro (it's free!)
2. Navigate to your region
3. Coordinates shown at bottom of screen
4. For bounding box:
   - Zoom to show your desired area
   - Note the lat/long at top-left corner (NW)
   - Note the lat/long at bottom-right corner (SE)

### Method 3: Online Tools
- https://www.latlong.net/
- https://boundingbox.klokantech.com/
- https://www.openstreetmap.org/ (right-click → Show address)

## Tips for Choosing Bounding Box

### Size Considerations
- **Too small** (< 0.1° x 0.1°): May have very few sensors
- **Too large** (> 1° x 1°): Too many sensors, cluttered maps
- **Ideal**: 0.2° - 0.5° on each side

### Checking Sensor Availability
Before committing to a long historical download:
1. Visit https://map.purpleair.com/
2. Zoom to your area
3. Count the purple sensor dots
4. Aim for 20-100 sensors for good coverage

### Latitude/Longitude Rules
- **Latitude**: Increases going North (+90 = North Pole, -90 = South Pole)
- **Longitude**: Increases going East (-180 to +180, 0 = Prime Meridian)
- **In BC**: All longitudes are negative (west of Prime Meridian)

So for bounding box:
- Northwest latitude > Southeast latitude (because north is "higher")
- Northwest longitude < Southeast longitude (more negative = further west)

### Example Validation
```python
BBOX = (49.35, -123.25, 49.00, -122.75)
         ^^^^   ^^^^^^   ^^^^   ^^^^^^
         NW_lat NW_lng   SE_lat SE_lng
```
Check:
- 49.35 > 49.00 ✓ (NW is north of SE)
- -123.25 < -122.75 ✓ (NW is west of SE)

## Testing Your Bounding Box

Use the test script to verify sensors exist:

```bash
export PURPLEAIR_API_KEY="your-key"
python3 test_purpleair_api.py
# Choose option 2 for custom bounding box
```

## Adjusting for Sensor Density

If you find:
- **Too few sensors** → Increase bounding box size
- **Too many sensors** → Decrease bounding box size
- **Sensors in wrong area** → Shift the coordinates

## Regional Air Quality Considerations

### Wildfire Smoke
Wider areas help track smoke movement:
```python
# Wide Fraser Valley for smoke tracking
BBOX = (49.50, -123.50, 48.80, -121.50)
```

### Urban Pollution
Tighter focus on urban core:
```python
# Downtown Vancouver focus
BBOX = (49.30, -123.20, 49.23, -123.00)
```

### Industrial Areas
Include both upwind and downwind sensors:
```python
# Port Metro Vancouver
BBOX = (49.35, -123.20, 49.20, -122.80)
```

## Coordinate Precision

Use 2 decimal places for degrees (≈ 1.1 km precision):
```python
BBOX = (49.35, -123.25, 49.00, -122.75)  # Good
BBOX = (49.3, -123.2, 49.0, -122.7)      # Also fine
BBOX = (49.3456, -123.2543, 49.0012, -122.7562)  # Unnecessary precision
```

## Saving Your Configurations

Create a config file for frequently-used regions:

```python
# my_regions.py

REGIONS = {
    'vancouver': (49.35, -123.25, 49.00, -122.75),
    'victoria': (48.55, -123.50, 48.40, -123.30),
    'kelowna': (50.05, -119.65, 49.80, -119.30),
    'whistler': (50.15, -123.00, 50.08, -122.90),
    'chilliwack': (49.20, -122.00, 49.10, -121.85),
}

# Use in your script:
# from my_regions import REGIONS
# BBOX = REGIONS['vancouver']
```
