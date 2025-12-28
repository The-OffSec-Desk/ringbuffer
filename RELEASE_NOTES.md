# RingBuffer v1.0.0

**Real-time Kernel Log & Telemetry Analyzer**

A professional Linux kernel log viewer for security researchers and kernel developers.

## Quick Start

### Option 1: Run Directly (No Installation)
```bash
chmod +x RingBuffer-x86_64.AppImage
./RingBuffer-x86_64.AppImage
```

### Option 2: Install Desktop Integration (Recommended)

For proper menu entry and icon display:
```bash
# Download both files to the same directory
chmod +x RingBuffer-x86_64.AppImage
bash install-icon.sh
```

This will:
- ✅ Install the RingBuffer icon
- ✅ Create a desktop menu entry
- ✅ Add RingBuffer to your application launcher

After installation, search for "RingBuffer" in your application menu.

## Features

- **Real-time kernel log monitoring** - Live streaming from `/dev/kmsg`
- **Advanced filtering** - Filter by severity, subsystem, keywords
- **Plugin system** - Extensible architecture for custom analyzers
- **USB event tracking** - Monitor device connections and disconnections
- **Beautiful UI** - Modern PySide6 interface with syntax highlighting
- **Zero installation** - Single portable executable

## Requirements

- **OS:** Linux x86_64 (any modern distribution)
- **Kernel:** 4.x or newer
- **Permissions:** Read access to `/dev/kmsg` (may require sudo or appropriate group membership)

## Verify Integrity
```bash
sha256sum -c RingBuffer-x86_64.AppImage.sha256
```

Expected output: `RingBuffer-x86_64.AppImage: OK`

## Uninstall
```bash
rm ~/.local/share/applications/ringbuffer.desktop
rm ~/.local/share/icons/hicolor/256x256/apps/ringbuffer.png
rm ~/.local/share/pixmaps/ringbuffer.png
gtk-update-icon-cache ~/.local/share/icons/hicolor/
```

## 📝 Running with Proper Permissions

To read kernel logs, you may need elevated permissions:
```bash
# Option 1: Run with sudo
sudo ./RingBuffer-x86_64.AppImage

# Option 2: Add your user to the appropriate group (recommended)
sudo usermod -aG systemd-journal $USER
# Log out and log back in for changes to take effect
```

## Troubleshooting

**Icon doesn't show in menu:**
- Run the install script: `bash install-icon.sh`
- Log out and log back in
- Update icon cache: `gtk-update-icon-cache ~/.local/share/icons/hicolor/`

**Permission denied when reading kernel logs:**
- Run with sudo or add your user to the `systemd-journal` group

**AppImage won't run:**
- Make sure it's executable: `chmod +x RingBuffer-x86_64.AppImage`
- Check if FUSE is installed: `sudo dnf install fuse` or `sudo apt install fuse`

## 📬 Support

Found a bug or have a feature request? [Open an issue](https://github.com/The-OffSec-Desk/kernel-log-gui/issues)

## 📄 License

[Your License Here]

---

**Made with ❤️ for the Linux community**
