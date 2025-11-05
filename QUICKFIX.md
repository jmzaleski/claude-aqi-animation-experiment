# Quick Fix for Installation Error

## The Problem
`pyproj` requires system libraries (PROJ, GEOS) that aren't installed on your system. 
The good news: **You don't need it!** The scripts work fine without map backgrounds.

## Quick Fix (Do This Now)

**Option 1: Use the fix script**
```bash
bash fix_install.sh
```

**Option 2: Manual install (core packages only)**
```bash
pip3 install requests pandas numpy matplotlib Pillow cachetools
```

**Option 3: If that fails, try with --user**
```bash
pip3 install --user requests pandas numpy matplotlib Pillow cachetools
```

## What You're Missing
Without cartopy/pyproj, you won't have automatic map backgrounds. But:
- ✓ All animation features work
- ✓ All AQI calculations work  
- ✓ You can add a georeferenced background image from CalTopo (as discussed)
- ✓ The visualizations look good with just the lat/lon grid

## If You Really Want Map Libraries

### On Ubuntu/Debian:
```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get install libgeos-dev libproj-dev

# Then install Python packages
pip3 install shapely pyproj cartopy
```

### On macOS:
```bash
# Install with Homebrew
brew install geos proj

# Then install Python packages  
pip3 install shapely pyproj cartopy
```

### On Windows WSL:
```bash
# Same as Ubuntu
sudo apt-get update
sudo apt-get install libgeos-dev libproj-dev
pip3 install shapely pyproj cartopy
```

## Verify Installation

Test that core packages work:
```bash
python3 -c "import requests, pandas, numpy, matplotlib; print('✓ Core packages OK!')"
```

Then test your API connection:
```bash
export PURPLEAIR_API_KEY='your-key-here'
python3 test_purpleair_api.py
```

## Run Your First Animation

Once core packages are installed:
```bash
# 3-day animation (quick test)
python3 purpleair_historical_animation.py --days 3 --hours-interval 2

# Full 7-day animation
python3 purpleair_historical_animation.py --days 7 --hours-interval 1
```

## Files You Need

**Minimum working setup requires:**
1. `requirements-core.txt` - Core dependencies only
2. Any of the `.py` scripts
3. Your PurpleAir API key

**For easy installation:**
- `fix_install.sh` - Emergency fix (run this now!)
- `setup_minimal.sh` - Minimal setup
- `requirements-core.txt` - Use this instead of requirements.txt

## Summary

The failure is just about optional mapping features. Your scripts will work perfectly fine for creating animations without them!

```bash
# This is all you need to do:
pip3 install requests pandas numpy matplotlib Pillow cachetools
export PURPLEAIR_API_KEY='your-key'  
python3 purpleair_historical_animation.py --days 7
```
