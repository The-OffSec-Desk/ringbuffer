"""
Main window implementation - Orchestrates all UI components
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon, QColor

from ui.menu_bar import MenuBarManager
from ui.filters_panel import FiltersPanel
from ui.event_stream import EventStreamWidget
from ui.context_panel import ContextPanel
from core.kernel_log_reader import KernelLogReader
from themes.dark_theme import apply_theme


class KernelLogMainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RingBuffer - Kernel Log Analyzer")
        icon = QIcon("public/placeholder-logo.svg")
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.setGeometry(100, 100, 1600, 1000)

        # Initialize core components
        self.kernel_reader = KernelLogReader()
        self.is_streaming = False

        # Build UI
        self._setup_ui()

        # Apply dark theme
        apply_theme(self)

        # Setup status bar with source indicator
        self._setup_status_bar()

        # Setup menu bar
        self.menu_manager = MenuBarManager(self)
        self.setMenuBar(self.menu_manager.create_menu_bar(self))

        # Setup live streaming timer
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self._on_stream_tick)
        self.stream_timer.setInterval(150)  # Poll every 150ms for lower latency

        # Auto-start live streaming on app launch
        self._init_and_start_stream()

    def _setup_ui(self):
        """Setup main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create main horizontal splitter (filters | stream)
        main_splitter = QSplitter(Qt.Horizontal)

        # Left: Filters panel
        self.filters_panel = FiltersPanel()
        self.filters_panel.filter_changed.connect(self._on_filter_changed)
        main_splitter.addWidget(self.filters_panel)

        # Right: Vertical splitter (stream | context)
        right_splitter = QSplitter(Qt.Vertical)

        # Center: Event stream
        self.event_stream = EventStreamWidget()
        self.event_stream.row_selected.connect(self._on_row_selected)
        right_splitter.addWidget(self.event_stream)

        # Bottom: Context panel
        self.context_panel = ContextPanel()
        right_splitter.addWidget(self.context_panel)

        # Set splitter sizes: 60% for stream, 40% for context
        right_splitter.setStretchFactor(0, 6)
        right_splitter.setStretchFactor(1, 4)

        main_splitter.addWidget(right_splitter)

        # Set splitter sizes: 20% for filters, 80% for right section
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 8)

        main_layout.addWidget(main_splitter)

        # Initial load
        self._load_initial_logs()

    def _setup_status_bar(self):
        """Setup status bar with source indicator"""
        self.status_label = QLabel("Initializing kernel log source...")
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #9CA3AF;
                background-color: #0B0F14;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
        """
        )
        self.statusBar().addWidget(self.status_label)

    def _load_initial_logs(self):
        """Load initial kernel logs on startup"""
        logs = self.kernel_reader.get_recent_logs(limit=100)
        self.event_stream.populate_logs(logs)

    def _init_and_start_stream(self):
        """Initialize engine and auto-start live streaming"""
        try:
            self.kernel_reader._initialize_engine_sync()

            # Update status bar with active source
            source_name = "Unknown"
            if self.kernel_reader.engine.source:
                source_obj = self.kernel_reader.engine.source
                if source_obj.__class__.__name__ == "DmesgSource":
                    source_name = "dmesg (live)"
                elif source_obj.__class__.__name__ == "JournalctlSource":
                    source_name = "journalctl (live)"

            self.status_label.setText(f"📡 Source: {source_name} | Streaming started")
            self.status_label.setStyleSheet(
                """
                QLabel {
                    color: #34D399;
                    background-color: #064E3B;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """
            )

            # Auto-start streaming
            self.start_live_stream()
        except Exception as e:
            self.status_label.setText(f"⚠️ Failed to initialize: {str(e)[:50]}")
            self.status_label.setStyleSheet(
                """
                QLabel {
                    color: #FCA5A5;
                    background-color: #7F1D1D;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """
            )

    @Slot()
    def _on_stream_tick(self):
        """Handle live streaming timer tick"""
        new_logs = self.kernel_reader.get_new_logs()
        if new_logs:
            self.event_stream.append_logs(new_logs)

    @Slot()
    def _on_filter_changed(self):
        """Handle filter changes"""
        filters = self.filters_panel.get_active_filters()
        self.event_stream.apply_filters(filters)

    def _on_row_selected(self, log_entry):
        """Handle row selection in event stream"""
        self.context_panel.set_log_entry(log_entry)

    def start_live_stream(self):
        """Start live log streaming"""
        self.is_streaming = True
        self.stream_timer.start()
        if self.status_label:
            self.status_label.setText(
                self.status_label.text().replace(
                    "Streaming started", "Streaming active ✓"
                )
            )

    def pause_stream(self):
        """Pause live log streaming"""
        self.is_streaming = False
        self.stream_timer.stop()
        if self.status_label:
            self.status_label.setText(
                self.status_label.text().replace("Streaming active ✓", "Paused ⏸️")
            )

    def resume_stream(self):
        """Resume live log streaming"""
        self.is_streaming = True
        self.stream_timer.start()
        if self.status_label:
            self.status_label.setText(
                self.status_label.text().replace("Paused ⏸️", "Streaming active ✓")
            )

    def clear_buffer_with_confirmation(self):
        """Clear kernel buffer with warning dialog"""
        reply = QMessageBox.warning(
            self,
            "Clear Kernel Buffer",
            "This will clear the kernel ring buffer. This action cannot be undone.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            success = self.kernel_reader.clear_buffer()
            if success:
                self.event_stream.clear_logs()
                QMessageBox.information(self, "Success", "Kernel buffer cleared.")
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to clear kernel buffer. Elevated permissions may be required.",
                )
