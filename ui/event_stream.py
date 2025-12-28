"""
Event stream widget - Central table view of kernel logs
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont


class EventStreamWidget(QWidget):
    """Main kernel event stream table"""
    
    row_selected = Signal(dict)
    
    SEVERITY_COLORS = {
        'EMERG': QColor('#DC2626'),
        'CRIT': QColor('#DC2626'),
        'ERR': QColor('#F87171'),
        'WARN': QColor('#FBBF24'),
        'INFO': QColor('#60A5FA'),
        'DEBUG': QColor('#34D399'),
    }
    
    def __init__(self):
        super().__init__()
        self.logs = []
        self.displayed_logs = []
        self.current_filters = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup event stream UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Severity", "Subsystem", "Message"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Configure columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Severity
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Subsystem
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Message
        
        # Style table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #111827;
                color: #E5E7EB;
                gridline-color: #1F2933;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1F2933;
            }
            QHeaderView::section {
                background-color: #0B0F14;
                color: #9CA3AF;
                padding: 4px;
                border: none;
                border-right: 1px solid #1F2933;
                border-bottom: 1px solid #1F2933;
            }
        """)
        
        # Connect selection
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        
        # Set monospace font for logs
        mono_font = QFont("JetBrains Mono")
        mono_font.setStyleStrategy(QFont.PreferAntialias)
        mono_font.setPointSize(9)
        self.table.setFont(mono_font)
        
        layout.addWidget(self.table)
    
    def populate_logs(self, logs):
        """Populate table with logs"""
        # Store full log set and compute displayed subset based on current filters
        self.logs = list(logs)
        if self.current_filters:
            display = [l for l in self.logs if self._matches(l, self.current_filters)]
        else:
            display = list(self.logs)

        self.displayed_logs = display
        self.table.setRowCount(len(display))

        for row, log in enumerate(display):
            self._add_log_row(row, log)
    
    def append_logs(self, logs):
        """Append new logs to the table"""
        if not logs:
            return

        # Always keep full logs history
        self.logs.extend(logs)

        start_row = self.table.rowCount()
        added_visible = 0

        for log in logs:
            if self.current_filters and not self._matches(log, self.current_filters):
                continue

            # insert a new visible row for each matching log
            self.table.insertRow(start_row + added_visible)
            self._add_log_row(start_row + added_visible, log)
            self.displayed_logs.append(log)
            added_visible += 1

        if added_visible:
            self.table.scrollToBottom()
    
    def _add_log_row(self, row, log):
        """Add a single log entry row"""
        # Display timestamp: prefer realtime ISO, then monotonic, then generic 'timestamp'
        ts_rt = log.get('timestamp_realtime')
        ts_mono = log.get('timestamp_monotonic')
        ts_generic = log.get('timestamp')

        if ts_rt:
            ts = ts_rt if isinstance(ts_rt, str) else str(ts_rt)
        elif isinstance(ts_mono, (int, float)):
            ts = f"{ts_mono:.6f}"
        elif ts_generic:
            ts = str(ts_generic)
        else:
            ts = 'N/A'

        timestamp_item = QTableWidgetItem(ts)

        severity_item = QTableWidgetItem(log.get('severity', 'INFO'))
        subsystem_item = QTableWidgetItem(str(log.get('subsystem') or 'KERNEL'))
        # show parsed message, fallback to raw if message empty
        message_item = QTableWidgetItem(log.get('message') or log.get('raw') or '')
        
        # Color severity
        severity = log.get('severity', 'INFO')
        color = self.SEVERITY_COLORS.get(severity, QColor('#9CA3AF'))
        severity_item.setForeground(color)
        
        # Make message monospace
        mono_font = QFont("JetBrains Mono", 9)
        message_item.setFont(mono_font)
        
        self.table.setItem(row, 0, timestamp_item)
        self.table.setItem(row, 1, severity_item)
        self.table.setItem(row, 2, subsystem_item)
        self.table.setItem(row, 3, message_item)
    
    def apply_filters(self, filters):
        """Apply filters to the log display"""
        # Store current filters and recompute displayed rows
        self.current_filters = filters or {}

        # Compute filtered subset
        display = [l for l in self.logs if self._matches(l, self.current_filters)]

        # Refresh table
        self.table.setRowCount(len(display))
        self.displayed_logs = display

        for row, log in enumerate(display):
            self._add_log_row(row, log)
    
    def clear_logs(self):
        """Clear all logs from display"""
        self.table.setRowCount(0)
        self.logs.clear()
    
    def _on_row_selected(self):
        """Handle row selection"""
        selected_rows = self.table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self.displayed_logs):
                self.row_selected.emit(self.displayed_logs[row])

    def _matches(self, log: dict, filters: dict) -> bool:
        """Return True if log matches provided filters."""
        if not filters:
            return True

        # Severities
        severities = filters.get('severities') or []
        if severities:
            sev = (log.get('severity') or '').upper()
            if sev not in severities:
                return False

        # Subsystems
        subs = filters.get('subsystems') or []
        if subs:
            subsystem = (log.get('subsystem') or '').upper()
            if subsystem not in [s.upper() for s in subs]:
                return False

        # Sources
        sources = filters.get('sources') or []
        if sources:
            source = (log.get('source') or '').lower()
            if source not in [s.lower() for s in sources]:
                return False

        # Search regex
        pattern = (filters.get('search_pattern') or '').strip()
        if pattern:
            try:
                import re

                if not re.search(pattern, (log.get('message') or ''), re.IGNORECASE):
                    return False
            except Exception:
                # If regex invalid, do not filter out results
                pass

        return True
