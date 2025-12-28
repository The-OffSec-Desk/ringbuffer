"""
Context panel implementation - Bottom detail view
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem
from PySide6.QtGui import QFont


class ContextPanel(QWidget):
    """Bottom panel with tabbed detailed information"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup context panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Tabbed interface
        self.tabs = QTabWidget()
        
        # Details tab
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        mono_font = QFont("JetBrains Mono", 9)
        self.details_text.setFont(mono_font)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                color: #E5E7EB;
                border: 1px solid #1F2933;
            }
        """)
        self.tabs.addTab(self.details_text, "Details")
        
        # Decoded tab
        self.decoded_text = QTextEdit()
        self.decoded_text.setReadOnly(True)
        self.decoded_text.setFont(QFont("Inter", 10))
        self.decoded_text.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                color: #E5E7EB;
                border: 1px solid #1F2933;
            }
        """)
        self.tabs.addTab(self.decoded_text, "Decoded")
        
        # Stack trace tab
        self.stack_trace_tree = QTreeWidget()
        self.stack_trace_tree.setColumnCount(1)
        self.stack_trace_tree.setHeaderLabels(["Stack Trace"])
        self.stack_trace_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #111827;
                color: #E5E7EB;
                border: 1px solid #1F2933;
            }
        """)
        self.tabs.addTab(self.stack_trace_tree, "Stack Trace")
        
        # Plugin output tab
        self.plugin_output = QTextEdit()
        self.plugin_output.setReadOnly(True)
        self.plugin_output.setFont(mono_font)
        self.plugin_output.setStyleSheet("""
            QTextEdit {
                background-color: #111827;
                color: #E5E7EB;
                border: 1px solid #1F2933;
            }
        """)
        self.tabs.addTab(self.plugin_output, "Plugin Output")
        
        # Style tabs
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: #1F2933;
                color: #9CA3AF;
                padding: 6px 12px;
                border: 1px solid #1F2933;
            }
            QTabBar::tab:selected {
                background-color: #111827;
                color: #E5E7EB;
                border-bottom: 2px solid #60A5FA;
            }
        """)
        
        layout.addWidget(self.tabs)
    
    def set_log_entry(self, log_entry):
        """Display a log entry in the context panel"""
        # Format timestamp: prefer realtime ISO, then monotonic
        ts_rt = log_entry.get('timestamp_realtime')
        ts_mono = log_entry.get('timestamp_monotonic')

        if ts_rt:
            ts = ts_rt if isinstance(ts_rt, str) else str(ts_rt)
        elif isinstance(ts_mono, (int, float)):
            ts = f"{ts_mono:.6f}"
        else:
            ts = 'N/A'
        
        # Details
        details = f"""Timestamp: {ts}
    Severity: {log_entry.get('severity', 'INFO')}
    Subsystem: {log_entry.get('subsystem', 'KERNEL')}

    Raw Message:
    {log_entry.get('raw', log_entry.get('message', 'N/A'))}

    Metadata:
    - CPU: {log_entry.get('cpu', 'None')}
    - PID: {log_entry.get('pid', 'None')}
    - Source: {log_entry.get('source', 'N/A')}
    """
        self.details_text.setText(details)
        
        # Decoded (placeholder)
        decoded = f"""Interpreted: {log_entry.get('message', 'N/A')}

This message indicates: [Decoded explanation would go here]
"""
        self.decoded_text.setText(decoded)
        
        # Stack trace
        self.stack_trace_tree.clear()
        self.stack_trace_tree.addTopLevelItem(
            QTreeWidgetItem(["[Stack trace would be displayed here]"])
        )
        
        # Plugin output
        self.plugin_output.setText("[Plugin annotations would appear here]")
