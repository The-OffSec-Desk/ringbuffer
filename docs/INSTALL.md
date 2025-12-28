# Installation Guide

This guide covers all methods for installing and running RingBuffer.

## Table of Contents

- [Quick Start (No Installation)](#quick-start-no-installation)
- [Desktop Integration](#desktop-integration)
- [System Requirements](#system-requirements)
- [Permissions Setup](#permissions-setup)
- [Building from Source](#building-from-source)
- [Troubleshooting](#troubleshooting)

---

## Quick Start (No Installation)

The fastest way to run RingBuffer - no installation required:
```bash
# Download the AppImage
curl -L -o RingBuffer-x86_64.AppImage \
  https://github.com/The-OffSec-Desk/ringbuffer/releases/latest/download/RingBuffer-x86_64.AppImage

# Make executable
chmod +x RingBuffer-x86_64.AppImage

# Run
./RingBuffer-x86_64.AppImage
```

**That's it!** RingBuffer will launch with all dependencies bundled.

---

## Desktop Integration

For a proper desktop experience with menu entry and icon:

### Automatic Installation (Recommended)
```bash
# Download both files
curl -L -o RingBuffer-x86_64.AppImage \
  https://github.com/The-OffSec-Desk/ringbuffer/releases/latest/download/RingBuffer-x86_64.AppImage

curl -L -o install-icon.sh \
  https://github.com/The-OffSec-Desk/ringbuffer/releases/latest/download/install-icon.sh

# Make executable
chmod +x RingBuffer-x86_64.AppImage

# Run installer
bash install-icon.sh
```

The installer will:
- ✅ Extract and install the application icon
- ✅ Create a desktop entry (`~/.local/share/applications/ringbuffer.desktop`)
- ✅ Add RingBuffer to your application menu
- ✅ Update system icon and desktop caches

After installation, search for "RingBuffer" in your application launcher.

### Manual Installation

If you prefer manual setup:
```bash
# Create directories
mkdir -p ~/.local/share/icons/hicolor/256x256/apps
mkdir -p ~/.local/share/applications

# Extract and install icon
./RingBuffer-x86_64.AppImage --appimage-extract usr/share/icons/hicolor/256x256/apps/ringbuffer.png
cp squashfs-root/usr/share/icons/hicolor/256x256/apps/ringbuffer.png \
   ~/.local/share/icons/hicolor/256x256/apps/
rm -rf squashfs-root

# Get absolute path to AppImage
APPIMAGE_PATH=$(readlink -f RingBuffer-x86_64.AppImage)

# Create desktop entry
cat > ~/.local/share/applications/ringbuffer.desktop << DESKTOP
[Desktop Entry]
Type=Application
Name=RingBuffer
Comment=Real-time Kernel Log & Telemetry Analyzer
Exec=env RINGBUFFER_ICON="$HOME/.local/share/icons/hicolor/256x256/apps/ringbuffer.png" "$APPIMAGE_PATH" %F
Icon=$HOME/.local/share/icons/hicolor/256x256/apps/ringbuffer.png
Terminal=false
Categories=System;
StartupNotify=true
DESKTOP

# Make desktop entry executable
chmod +x ~/.local/share/applications/ringbuffer.desktop

# Update caches
gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

### Uninstallation

To remove RingBuffer:
```bash
# Remove desktop integration
rm ~/.local/share/applications/ringbuffer.desktop
rm ~/.local/share/icons/hicolor/256x256/apps/ringbuffer.png

# Update caches
gtk-update-icon-cache ~/.local/share/icons/hicolor/
update-desktop-database ~/.local/share/applications/

# Remove AppImage
rm RingBuffer-x86_64.AppImage
```

---

## System Requirements

### Minimum Requirements

- **Operating System:** Linux x86_64 (any modern distribution)
- **Kernel Version:** 4.x or newer (for kernel log access)
- **Architecture:** 64-bit (x86_64)
- **RAM:** 256 MB minimum, 512 MB recommended
- **Disk Space:** 200 MB for AppImage + runtime space

### Supported Distributions

RingBuffer has been tested on:
- ✅ Fedora 38+
- ✅ Ubuntu 20.04+
- ✅ Debian 11+
- ✅ Arch Linux
- ✅ openSUSE Leap 15+
- ✅ Linux Mint 20+

Should work on any modern Linux distribution with:
- Kernel 4.x or newer
- glibc 2.28+
- FUSE support (for AppImage)
- X11 or Wayland display server

### Installing FUSE

If AppImage won't run, you may need FUSE:
```bash
# Fedora/RHEL/CentOS
sudo dnf install fuse

# Debian/Ubuntu
sudo apt install fuse

# Arch Linux
sudo pacman -S fuse2

# openSUSE
sudo zypper install fuse
```

---

## Permissions Setup

RingBuffer reads kernel logs from `/dev/kmsg` (via dmesg) or systemd journal (via journalctl), which requires appropriate permissions.

### Option 1: Run with sudo (Quick Test)
```bash
sudo ./RingBuffer-x86_64.AppImage
```

**Pros:** Immediate access
**Cons:** Not recommended for regular use, security implications

### Option 2: Add User to systemd-journal Group (Recommended)
```bash
# Add your user to the systemd-journal group
sudo usermod -aG systemd-journal $USER

# Verify the change
groups $USER

# Log out and log back in for changes to take effect
```

After logging back in, you can run RingBuffer without sudo.

### Option 3: Create kmsg Group (Alternative)
```bash
# Create kmsg group
sudo groupadd -f kmsg

# Add your user
sudo usermod -aG kmsg $USER

# Create udev rule
sudo tee /etc/udev/rules.d/99-kmsg.rules << 'RULE'
KERNEL=="kmsg", GROUP="kmsg", MODE="0640"
RULE

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Log out and log back in
```

### Checking Permissions

RingBuffer includes a permission checker. From the Settings menu:
- Menu → **Settings → Check Permissions**

This will show which log sources are available and working.

---

## Building from Source

### Prerequisites
```bash
# Install Python 3.10+
python3 --version  # Should show 3.10 or higher

# Install pip
sudo dnf install python3-pip  # Fedora
sudo apt install python3-pip  # Ubuntu/Debian

# Install PySide6 (Qt for Python)
pip3 install PySide6

# Install development tools (optional, for building extensions)
sudo dnf install gcc python3-devel  # Fedora
sudo apt install build-essential python3-dev  # Ubuntu/Debian
```

### Clone and Setup
```bash
# Clone repository
git clone https://github.com/The-OffSec-Desk/ringbuffer.git
cd ringbuffer

# The application uses only standard library modules plus PySide6
# No additional dependencies required for basic functionality
```

### Run from Source
```bash
# Run application directly
python3 main.py
```

### Building AppImage

AppImage building requires additional tools and is typically done by maintainers. The AppImage includes:
- Python 3.13 runtime
- PySide6 Qt libraries
- All required system libraries
- The complete RingBuffer application

---

## Troubleshooting

### AppImage Won't Run

**Error:** `cannot execute binary file`
**Solution:** Make sure the file is executable
```bash
chmod +x RingBuffer-x86_64.AppImage
```

**Error:** `AppImage cannot be mounted`
**Solution:** Install FUSE (see [Installing FUSE](#installing-fuse))

**Error:** `fuse: failed to exec fusermount`
**Solution:**
```bash
# Make sure FUSE is properly installed
which fusermount
sudo chmod u+s /usr/bin/fusermount
```

### Permission Errors

**Error:** `Permission denied: '/dev/kmsg'` or `dmesg: read kernel buffer failed: Operation not permitted`
**Solution:** See [Permissions Setup](#permissions-setup) section

**Error:** `journalctl: permission denied`
**Solution:** Check if you're in the correct group
```bash
groups | grep -E "systemd-journal|kmsg"
```

### Application Won't Start

**Error:** Qt/GUI related errors
**Solution:**
1. Ensure you have a display server running (X11 or Wayland)
2. Try running with different Qt platform:
```bash
export QT_QPA_PLATFORM=xcb ./RingBuffer-x86_64.AppImage  # Force X11
export QT_QPA_PLATFORM=wayland ./RingBuffer-x86_64.AppImage  # Force Wayland
```

**Error:** Python/import errors
**Solution:** The AppImage should be self-contained. If running from source:
```bash
pip3 install PySide6
```

### No Logs Appearing

**Problem:** No kernel events in the table
**Solution:**
1. Check permissions (see above)
2. Verify kernel log sources are available:
```bash
   # Test dmesg access
   dmesg | tail -5

   # Test journalctl access
   journalctl -k -n 5
```
3. Check status bar in RingBuffer - it shows the active source
4. Try running with `sudo` to test permissions

### Icon Issues

**Problem:** Icon doesn't show in application menu
**Solution:**
```bash
# Re-run the install script
bash install-icon.sh

# Manually update caches
gtk-update-icon-cache ~/.local/share/icons/hicolor/
update-desktop-database ~/.local/share/applications/

# Log out and log back in
```

**Problem:** Generic icon in taskbar
**Solution:** This is usually fixed by logging out and back in after installation

### Performance Issues

**Problem:** High CPU usage or slow UI
**Solution:**
1. Enable more restrictive filters to reduce event volume
2. The polling interval is fixed at 150ms - no user configuration available
3. Close other resource-intensive applications

### Getting Help

If you encounter issues not covered here:

1. Check existing [GitHub Issues](https://github.com/The-OffSec-Desk/ringbuffer/issues)
2. Search [GitHub Discussions](https://github.com/The-OffSec-Desk/ringbuffer/discussions)
3. Open a new issue with:
   - Your Linux distribution and version (`cat /etc/os-release`)
   - Kernel version (`uname -r`)
   - Error messages (full output from terminal)
   - Steps to reproduce
   - Whether you're using AppImage or running from source

---

## Advanced Configuration

### Custom Installation Location

You can place the AppImage anywhere:
```bash
# Install to /opt (system-wide)
sudo mv RingBuffer-x86_64.AppImage /opt/
sudo chmod 755 /opt/RingBuffer-x86_64.AppImage

# Create system-wide desktop entry
sudo cp ~/.local/share/applications/ringbuffer.desktop /usr/share/applications/
```

### Multiple Versions

You can run multiple versions side-by-side:
```bash
mv RingBuffer-x86_64.AppImage RingBuffer-v1.0.0.AppImage
# Download new version
curl -L -o RingBuffer-latest.AppImage ...
```

Each AppImage is self-contained and won't conflict.

### Environment Variables

RingBuffer respects these environment variables:
- `RINGBUFFER_ICON`: Path to custom icon file
- `QT_QPA_PLATFORM`: Force Qt platform (xcb/wayland)
- `DISPLAY`: X11 display (if using X11)

---

## Next Steps

- Read the [User Manual](MANUAL.md) to learn how to use RingBuffer
- Explore [Plugin Development](PLUGINS.md) to extend functionality

---

**Need help?** Open an issue on [GitHub](https://github.com/The-OffSec-Desk/ringbuffer/issues)