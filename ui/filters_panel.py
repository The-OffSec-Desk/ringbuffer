"""
Filters panel implementation - Left sidebar
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal


SEVERITY_LEVELS = ["EMERG", "ALERT", "CRIT", "ERR", "WARN", "NOTICE", "INFO", "DEBUG"]
SUBSYSTEMS = [
    "USB",
    "MEMORY",
    "NETWORK",
    "FILESYSTEM",
    "DRM",
    "SECURITY",
    "AUDIO",
    "HID",
]
SOURCES = [("Ring Buffer (dmesg)", "dmesg"), ("systemd-journal", "journalctl")]


class FiltersPanel(QWidget):
    """Left sidebar with filtering controls"""

    filter_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setMaximumWidth(260)
        self.setMinimumWidth(200)

        self.severity_checks = {}
        self.subsystem_checks = {}
        self.source_checks = {}  # Maps display_name -> (checkbox, actual_value)

        self._setup_ui()

    def _setup_ui(self):
        """Setup filters panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Severity filters
        severity_group = QGroupBox("Severity")
        severity_layout = QVBoxLayout()
        severity_layout.setSpacing(4)

        for level in SEVERITY_LEVELS:
            checkbox = QCheckBox(level)
            checkbox.stateChanged.connect(lambda: self.filter_changed.emit())
            severity_layout.addWidget(checkbox)
            self.severity_checks[level] = checkbox

        severity_group.setLayout(severity_layout)
        layout.addWidget(severity_group)

        # Subsystem filters
        subsystem_group = QGroupBox("Subsystem")
        subsystem_layout = QVBoxLayout()
        subsystem_layout.setSpacing(4)

        subsystem_scroll = QScrollArea()
        subsystem_widget = QWidget()
        subsystem_inner_layout = QVBoxLayout(subsystem_widget)
        subsystem_inner_layout.setSpacing(4)

        for subsys in SUBSYSTEMS:
            checkbox = QCheckBox(subsys)
            checkbox.stateChanged.connect(lambda: self.filter_changed.emit())
            subsystem_inner_layout.addWidget(checkbox)
            self.subsystem_checks[subsys] = checkbox

        subsystem_inner_layout.addStretch()
        subsystem_scroll.setWidget(subsystem_widget)
        subsystem_scroll.setWidgetResizable(True)
        subsystem_layout.addWidget(subsystem_scroll)
        subsystem_group.setLayout(subsystem_layout)
        layout.addWidget(subsystem_group)

        # Source filters
        source_group = QGroupBox("Source")
        source_layout = QVBoxLayout()
        source_layout.setSpacing(4)

        for display_name, actual_value in SOURCES:
            checkbox = QCheckBox(display_name)
            checkbox.stateChanged.connect(lambda: self.filter_changed.emit())
            source_layout.addWidget(checkbox)
            self.source_checks[actual_value] = checkbox

        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # Search box
        search_group = QGroupBox("Search (Regex)")
        search_layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter regex pattern...")
        self.search_input.textChanged.connect(lambda: self.filter_changed.emit())
        search_layout.addWidget(self.search_input)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(clear_btn)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        layout.addStretch()

    def get_active_filters(self):
        """Get current active filters"""
        return {
            "severities": [
                lvl for lvl, cb in self.severity_checks.items() if cb.isChecked()
            ],
            "subsystems": [
                sub for sub, cb in self.subsystem_checks.items() if cb.isChecked()
            ],
            "sources": [
                src for src, cb in self.source_checks.items() if cb.isChecked()
            ],
            "search_pattern": self.search_input.text(),
        }

    def _clear_search(self):
        """Clear search input"""
        self.search_input.clear()
