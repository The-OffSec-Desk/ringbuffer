#!/usr/bin/env python3
"""
Advanced Kernel Log GUI - Main Entry Point
A professional Linux kernel log viewer for security researchers and kernel developers.
"""
import logging
import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import KernelLogMainWindow


def get_icon_path():
    """Find the application icon in various possible locations."""
    # Check if icon path was provided by desktop launcher
    if "RINGBUFFER_ICON" in os.environ:
        icon = Path(os.environ["RINGBUFFER_ICON"])
        if icon.exists():
            return str(icon)

    # When running from AppImage
    if "APPIMAGE" in os.environ or "APPDIR" in os.environ:
        appdir = Path(os.environ.get("APPDIR", ""))
        icon = appdir / "usr/share/icons/hicolor/256x256/apps/ringbuffer.png"
        if icon.exists():
            return str(icon)

    # Possible icon locations
    possible_paths = [
        Path(__file__).parent / "ringbuffer.png",  # Project root
        Path.home()
        / ".local/share/icons/hicolor/256x256/apps/ringbuffer.png",  # User install
        Path.home() / ".local/share/pixmaps/ringbuffer.png",  # Alt user install
        Path("/usr/share/icons/hicolor/256x256/apps/ringbuffer.png"),  # System install
        Path("/usr/share/pixmaps/ringbuffer.png"),  # Alt system install
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    return None


def main():
    # Enable debug logging to see what's happening during initialization
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting Kernel Log GUI...")

    app = QApplication(sys.argv)

    # Set application metadata (IMPORTANT for taskbar)
    app.setApplicationName("RingBuffer")
    app.setApplicationDisplayName("RingBuffer")
    app.setDesktopFileName("ringbuffer.desktop")
    app.setOrganizationName("RingBuffer")
    app.setOrganizationDomain("ringbuffer.app")

    app.setStyle("Fusion")  # Use Fusion style for cross-platform consistency

    # Set application icon
    icon_path = get_icon_path()
    if icon_path:
        logger.info(f"Setting application icon from: {icon_path}")
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
    else:
        logger.warning("Could not find application icon")

    window = KernelLogMainWindow()

    # Set window icon directly (redundant but helps with some window managers)
    if icon_path:
        window.setWindowIcon(QIcon(icon_path))

    # Set window title if not already set
    if not window.windowTitle() or window.windowTitle() == "":
        window.setWindowTitle("RingBuffer - Kernel Log Analyzer")

    window.show()

    logger.info("GUI window displayed")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
