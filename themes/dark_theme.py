"""
Dark theme stylesheet and theming utilities
"""

DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #0B0F14;
    color: #E5E7EB;
}

QWidget {
    background-color: #0B0F14;
    color: #E5E7EB;
}

QMenuBar {
    background-color: #111827;
    color: #E5E7EB;
    border-bottom: 1px solid #1F2933;
}

QMenuBar::item:selected {
    background-color: #1F2933;
}

QMenu {
    background-color: #111827;
    color: #E5E7EB;
    border: 1px solid #1F2933;
}

QMenu::item:selected {
    background-color: #1F2933;
}

QGroupBox {
    color: #E5E7EB;
    border: 1px solid #1F2933;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

QCheckBox {
    color: #E5E7EB;
    spacing: 5px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QCheckBox::indicator:unchecked {
    background-color: #1F2933;
    border: 1px solid #374151;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #60A5FA;
    border: 1px solid #3B82F6;
    border-radius: 3px;
}

QLineEdit {
    background-color: #1F2933;
    color: #E5E7EB;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 4px;
}

QLineEdit:focus {
    border: 1px solid #60A5FA;
    outline: none;
}

QPushButton {
    background-color: #1F2933;
    color: #E5E7EB;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #374151;
}

QPushButton:pressed {
    background-color: #4B5563;
}

QScrollArea {
    background-color: #0B0F14;
    border: none;
}

QScrollBar:vertical {
    background-color: #0B0F14;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #374151;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4B5563;
}

QSplitter::handle {
    background-color: #1F2933;
}

QSplitter::handle:hover {
    background-color: #374151;
}
"""


def apply_theme(application):
    """Apply dark theme to the entire application"""
    application.setStyleSheet(DARK_THEME_STYLESHEET)
