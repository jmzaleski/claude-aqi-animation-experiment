#!/bin/bash
# Emergency Fix - Run this if setup.sh failed
# This installs only the packages that definitely work

echo "=================================================="
echo "Emergency Fix - Installing Core Packages Only"
echo "=================================================="
echo ""

echo "Uninstalling any partially-installed packages..."
pip3 uninstall -y pyproj cartopy shapely 2>/dev/null

echo ""
echo "Installing core dependencies (this will work)..."
pip3 install requests pandas numpy matplotlib Pillow cachetools

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Success! Core packages installed."
    echo ""
    echo "Your scripts will work now. You're just missing optional map features."
    echo ""
    echo "Next steps:"
    echo "1. export PURPLEAIR_API_KEY='your-key-here'"
    echo "2. python3 test_purpleair_api.py"
    echo "3. python3 purpleair_historical_animation.py --days 7"
    echo ""
else
    echo ""
    echo "Still having issues? Try with --user flag:"
    echo "  pip3 install --user requests pandas numpy matplotlib Pillow cachetools"
    echo ""
    echo "Or with --break-system-packages:"
    echo "  pip3 install --break-system-packages requests pandas numpy matplotlib Pillow cachetools"
fi
