#!/bin/bash
# Make Animation from PNG Frames
# Creates both GIF and MP4 from the frame files

# Output directory configuration
DIR="/tmp/purple-air"
FRAMES_DIR="${DIR}/frames"
FPS=4  # Frames per second

echo "================================================================"
echo "Creating Animation from PNG Frames"
echo "================================================================"
echo ""

# Check frames exist
if [ ! -d "$FRAMES_DIR" ] || [ -z "$(ls -A $FRAMES_DIR/frame_*.png 2>/dev/null)" ]; then
    echo "Error: No frames found in $FRAMES_DIR"
    echo "Run purpleair_efficient.py first to create frames"
    exit 1
fi

FRAME_COUNT=$(ls -1 $FRAMES_DIR/frame_*.png 2>/dev/null | wc -l)
echo "Found $FRAME_COUNT frames in $FRAMES_DIR"
echo ""

# Option 1: Create MP4 with ffmpeg (best quality, small file)
if command -v ffmpeg &> /dev/null; then
    echo "Creating MP4 video with ffmpeg..."
    ffmpeg -y -framerate $FPS -pattern_type glob -i "$FRAMES_DIR/frame_*.png" \
           -c:v libx264 -pix_fmt yuv420p -crf 23 \
           "$DIR/aqi_animation.mp4" 2>&1 | grep -v "^frame="
    
    if [ -f "$DIR/aqi_animation.mp4" ]; then
        SIZE=$(du -h "$DIR/aqi_animation.mp4" | cut -f1)
        echo "✓ Created: $DIR/aqi_animation.mp4 ($SIZE)"
    else
        echo "✗ Failed to create MP4"
    fi
    echo ""
else
    echo "ffmpeg not found - skipping MP4 creation"
    echo "Install with: brew install ffmpeg"
    echo ""
fi

# Option 2: Create GIF with ImageMagick (larger file, works everywhere)
if command -v convert &> /dev/null; then
    echo "Creating GIF with ImageMagick..."
    
    # Calculate delay (100 = 1 second, so 100/fps = delay)
    DELAY=$((100 / FPS))
    
    convert -monitor -delay $DELAY -loop 0 $FRAMES_DIR/frame_*.png "$DIR/aqi_animation.gif"
    
    if [ -f "$DIR/aqi_animation.gif" ]; then
        SIZE=$(du -h "$DIR/aqi_animation.gif" | cut -f1)
        echo "✓ Created: $DIR/aqi_animation.gif ($SIZE)"
    else
        echo "✗ Failed to create GIF"
    fi
    echo ""
else
    echo "ImageMagick (convert) not found - skipping GIF creation"
    echo "Install with: brew install imagemagick"
    echo ""
fi

# Option 3: Create optimized/smaller GIF with ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "Creating optimized GIF with ffmpeg..."
    ffmpeg -y -framerate $FPS -pattern_type glob -i "$FRAMES_DIR/frame_*.png" \
           -vf "scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
           "$DIR/aqi_animation_optimized.gif" 2>&1 | grep -v "^frame="
    
    if [ -f "$DIR/aqi_animation_optimized.gif" ]; then
        SIZE=$(du -h "$DIR/aqi_animation_optimized.gif" | cut -f1)
        echo "✓ Created: $DIR/aqi_animation_optimized.gif ($SIZE)"
    fi
    echo ""
fi

echo "================================================================"
echo "Complete!"
echo "================================================================"
echo ""

# Show what was created
echo "Output files:"
ls -lh "$DIR"/aqi_animation* 2>/dev/null | awk '{print "  "$9" - "$5}'

echo ""
echo "View with:"
echo "  open $DIR/aqi_animation.mp4"
echo "  open $DIR/aqi_animation.gif"
