"""
Menu bar implementation
"""

from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox, QFileDialog
from PySide6.QtCore import Qt


class MenuBarManager:
    """Manages menu bar and menu actions"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def create_menu_bar(self, parent):
        """Create and populate the menu bar"""
        menu_bar = QMenuBar(parent)
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        export_raw_action = file_menu.addAction("Export Logs (Raw)")
        export_raw_action.triggered.connect(self._export_raw_logs)
        
        export_filtered_action = file_menu.addAction("Export Logs (Filtered)")
        export_filtered_action.triggered.connect(self._export_filtered_logs)
        
        file_menu.addSeparator()
        
        clear_action = file_menu.addAction("Clear Kernel Buffer")
        clear_action.triggered.connect(self.main_window.clear_buffer_with_confirmation)
        clear_action.setShortcut("Ctrl+Shift+Delete")
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.main_window.close)
        exit_action.setShortcut("Ctrl+Q")
        
        # Capture menu
        capture_menu = menu_bar.addMenu("Capture")
        
        start_action = capture_menu.addAction("Start Live Stream")
        start_action.triggered.connect(self.main_window.start_live_stream)
        start_action.setShortcut("Space")
        
        pause_action = capture_menu.addAction("Pause Stream")
        pause_action.triggered.connect(self.main_window.pause_stream)
        pause_action.setShortcut("Ctrl+Space")
        
        resume_action = capture_menu.addAction("Resume Stream")
        resume_action.triggered.connect(self.main_window.resume_stream)
        resume_action.setShortcut("Ctrl+Shift+Space")
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        toggle_ts_action = view_menu.addAction("Toggle Timestamp Format")
        toggle_ts_action.triggered.connect(self._toggle_timestamp_format)
        toggle_ts_action.setShortcut("Ctrl+T")
        
        toggle_autoscroll_action = view_menu.addAction("Toggle Auto-Scroll")
        toggle_autoscroll_action.triggered.connect(self._toggle_autoscroll)
        toggle_autoscroll_action.setShortcut("Ctrl+A")
        
        # Plugins menu
        plugins_menu = menu_bar.addMenu("Plugins")
        plugins_menu.addAction("Enable / Disable Plugins")
        
        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        theme_action = settings_menu.addAction("Theme (Dark)")
        theme_action.triggered.connect(self._show_theme_dialog)
        
        perms_action = settings_menu.addAction("Check Permissions")
        perms_action.triggered.connect(self._check_permissions)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)
        
        docs_action = help_menu.addAction("Documentation")
        docs_action.triggered.connect(self._show_docs)
        
        return menu_bar
    
    def _export_raw_logs(self):
        """Export raw kernel logs"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Export Raw Logs",
            "",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        if file_path:
            # Implementation would export logs
            pass
    
    def _export_filtered_logs(self):
        """Export filtered kernel logs"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Export Filtered Logs",
            "",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        if file_path:
            # Implementation would export filtered logs
            pass
    
    def _toggle_timestamp_format(self):
        """Toggle between monotonic and real timestamp format"""
        # Implementation would toggle timestamp display
        pass
    
    def _toggle_autoscroll(self):
        """Toggle auto-scroll behavior"""
        # Implementation would toggle autoscroll
        pass
    
    def _show_theme_dialog(self):
        """Show theme selection dialog"""
        QMessageBox.information(self.main_window, "Theme", "Dark theme is currently active.")
    
    def _check_permissions(self):
        """Check and display permission status"""
        QMessageBox.information(
            self.main_window,
            "Permissions",
            "Running as standard user. Elevated access may be required for some operations."
        )
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self.main_window,
            "About Kernel Log Viewer",
            "Advanced Kernel Log GUI v1.0\n\n"
            "A professional tool for analyzing Linux kernel logs.\n"
            "Designed for kernel developers, security researchers, and Linux power users."
        )
    
    def _show_docs(self):
        """Show documentation"""
        QMessageBox.information(
            self.main_window,
            "Documentation",
            "Documentation and help resources are available at:\n"
            "https://github.com/The-OffSec-Desk/ringbuffer"
        )
