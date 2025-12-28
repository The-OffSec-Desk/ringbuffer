#!/bin/bash
# RingBuffer Desktop Integration Installer

set -e

APPIMAGE="./RingBuffer-x86_64.AppImage"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
PIXMAPS_DIR="$HOME/.local/share/pixmaps"
DESKTOP_DIR="$HOME/.local/share/applications"

# Check if AppImage exists
if [ ! -f "$APPIMAGE" ]; then
    echo "Error: RingBuffer-x86_64.AppImage not found in current directory"
    exit 1
fi

echo "Installing RingBuffer desktop integration..."

# Extract icon
echo "  → Extracting icon..."
"$APPIMAGE" --appimage-extract usr/share/icons/hicolor/256x256/apps/ringbuffer.png >/dev/null 2>&1

# Install icon to multiple locations for better compatibility
mkdir -p "$ICON_DIR"
mkdir -p "$PIXMAPS_DIR"

cp squashfs-root/usr/share/icons/hicolor/256x256/apps/ringbuffer.png "$ICON_DIR/"
cp squashfs-root/usr/share/icons/hicolor/256x256/apps/ringbuffer.png "$PIXMAPS_DIR/"

rm -rf squashfs-root

# Get absolute path to AppImage
APPIMAGE_PATH=$(readlink -f "$APPIMAGE")

# Create desktop entry with environment variable for icon path
echo "  → Creating desktop entry..."
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/ringbuffer.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=RingBuffer
Comment=Real-time Kernel Log & Telemetry Analyzer
Exec=env RINGBUFFER_ICON="$ICON_DIR/ringbuffer.png" "$APPIMAGE_PATH" %F
Icon=$ICON_DIR/ringbuffer.png
Terminal=false
Categories=System;
StartupNotify=true
DESKTOP

# Make desktop entry executable
chmod +x "$DESKTOP_DIR/ringbuffer.desktop"

# Update caches
echo "  → Updating system caches..."
gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo ""
echo "✓ Installation complete!"
echo ""
echo "RingBuffer is now installed. The icon should appear correctly."
echo "If the icon doesn't show immediately, try logging out and back in."
echo ""
echo "To uninstall:"
echo "  rm ~/.local/share/applications/ringbuffer.desktop"
echo "  rm ~/.local/share/icons/hicolor/256x256/apps/ringbuffer.png"
echo "  rm ~/.local/share/pixmaps/ringbuffer.png"
