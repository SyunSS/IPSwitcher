"""
Qt stylesheets for IP Switcher – light and dark themes with Windows 11 Fluent aesthetics.
"""

LIGHT_STYLE = """
/* ── Global ────────────────────────────────────────────────────── */
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
    color: #1a1a1a;
    background-color: #f3f3f3;
}

QMainWindow {
    background-color: #f3f3f3;
}

/* ── Frames / Cards ─────────────────────────────────────────────── */
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

/* ── Labels ─────────────────────────────────────────────────────── */
QLabel#title {
    font-size: 20px;
    font-weight: 600;
    color: #1a1a1a;
}

QLabel#badge_admin {
    background-color: #107c10;
    color: #ffffff;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#badge_noadmin {
    background-color: #d83b01;
    color: #ffffff;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#section_title {
    font-size: 12px;
    font-weight: 600;
    color: #605e5c;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#detail_label {
    color: #605e5c;
    font-size: 12px;
}

QLabel#detail_value {
    color: #1a1a1a;
    font-weight: 500;
}

QLabel#ip_info {
    color: #0078d4;
    font-weight: 600;
    font-size: 13px;
}

QLabel#adapter_status_enabled {
    color: #107c10;
    font-weight: 600;
    font-size: 12px;
}

QLabel#adapter_status_disabled {
    color: #d83b01;
    font-weight: 600;
    font-size: 12px;
}

QLabel#adapter_status_unknown {
    color: #605e5c;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#btn_enable {
    background-color: #107c10;
    color: #ffffff;
}

QPushButton#btn_enable:hover {
    background-color: #0b6b0b;
}

QPushButton#btn_enable:disabled {
    background-color: #c8c6c4;
    color: #a19f9d;
}

/* ── ComboBox ────────────────────────────────────────────────────── */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #c8c6c4;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 28px;
    selection-background-color: #0078d4;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox:focus {
    border: 2px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #605e5c;
    width: 0;
    height: 0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c8c6c4;
    border-radius: 4px;
    selection-background-color: #cce4f7;
    selection-color: #1a1a1a;
    outline: none;
}

/* ── List Widget ─────────────────────────────────────────────────── */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #f0f0f0;
    border-radius: 0px;
}

QListWidget::item:selected {
    background-color: #cce4f7;
    color: #1a1a1a;
    border-left: 3px solid #0078d4;
}

QListWidget::item:hover:!selected {
    background-color: #f5f5f5;
}

/* ── Push Buttons ────────────────────────────────────────────────── */
QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 500;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #c8c6c4;
    color: #a19f9d;
}

QPushButton#btn_secondary {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #c8c6c4;
}

QPushButton#btn_secondary:hover {
    background-color: #f5f5f5;
    border-color: #0078d4;
}

QPushButton#btn_secondary:pressed {
    background-color: #e8e8e8;
}

QPushButton#btn_danger {
    background-color: #d83b01;
    color: #ffffff;
}

QPushButton#btn_danger:hover {
    background-color: #c43301;
}

QPushButton#btn_danger:pressed {
    background-color: #a42c00;
}

/* ── Line Edit ───────────────────────────────────────────────────── */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c8c6c4;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 28px;
}

QLineEdit:focus {
    border: 2px solid #0078d4;
}

QLineEdit:disabled {
    background-color: #f3f3f3;
    color: #a19f9d;
}

/* ── Text Edit (log area) ────────────────────────────────────────── */
QTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
}

/* ── Scroll Bar ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #c8c6c4;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #a19f9d;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #e0e0e0;
    width: 1px;
}

/* ── Dialog ──────────────────────────────────────────────────────── */
QDialog {
    background-color: #f3f3f3;
}
"""

DARK_STYLE = """
/* ── Global ────────────────────────────────────────────────────── */
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
    color: #ffffff;
    background-color: #202020;
}

QMainWindow {
    background-color: #202020;
}

/* ── Frames / Cards ─────────────────────────────────────────────── */
QFrame#card {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
}

/* ── Labels ─────────────────────────────────────────────────────── */
QLabel#title {
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#badge_admin {
    background-color: #107c10;
    color: #ffffff;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#badge_noadmin {
    background-color: #d83b01;
    color: #ffffff;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#section_title {
    font-size: 12px;
    font-weight: 600;
    color: #9d9d9d;
    letter-spacing: 0.5px;
}

QLabel#detail_label {
    color: #9d9d9d;
    font-size: 12px;
}

QLabel#detail_value {
    color: #ffffff;
    font-weight: 500;
}

QLabel#ip_info {
    color: #4ec9b0;
    font-weight: 600;
    font-size: 13px;
}

QLabel#adapter_status_enabled {
    color: #4ec952;
    font-weight: 600;
    font-size: 12px;
}

QLabel#adapter_status_disabled {
    color: #f44747;
    font-weight: 600;
    font-size: 12px;
}

QLabel#adapter_status_unknown {
    color: #9d9d9d;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#btn_enable {
    background-color: #107c10;
    color: #ffffff;
}

QPushButton#btn_enable:hover {
    background-color: #0b6b0b;
}

QPushButton#btn_enable:disabled {
    background-color: #4a4a4a;
    color: #6e6e6e;
}

/* ── ComboBox ────────────────────────────────────────────────────── */
QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 28px;
    color: #ffffff;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox:focus {
    border: 2px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #9d9d9d;
    width: 0;
    height: 0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    outline: none;
}

/* ── List Widget ─────────────────────────────────────────────────── */
QListWidget {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    outline: none;
    color: #ffffff;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #3a3a3a;
}

QListWidget::item:selected {
    background-color: #004e8c;
    color: #ffffff;
    border-left: 3px solid #0078d4;
}

QListWidget::item:hover:!selected {
    background-color: #383838;
}

/* ── Push Buttons ────────────────────────────────────────────────── */
QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 500;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #4a4a4a;
    color: #6e6e6e;
}

QPushButton#btn_secondary {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #4a4a4a;
}

QPushButton#btn_secondary:hover {
    background-color: #484848;
}

QPushButton#btn_secondary:pressed {
    background-color: #2d2d2d;
}

QPushButton#btn_danger {
    background-color: #d83b01;
    color: #ffffff;
}

QPushButton#btn_danger:hover {
    background-color: #c43301;
}

/* ── Line Edit ───────────────────────────────────────────────────── */
QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 28px;
    color: #ffffff;
}

QLineEdit:focus {
    border: 2px solid #0078d4;
}

/* ── Text Edit ───────────────────────────────────────────────────── */
QTextEdit {
    background-color: #141414;
    color: #d4d4d4;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
}

/* ── Scroll Bar ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #4a4a4a;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #6e6e6e;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #3a3a3a;
    width: 1px;
}

/* ── Dialog ──────────────────────────────────────────────────────── */
QDialog {
    background-color: #202020;
}
"""


def get_style(dark: bool = False) -> str:
    return DARK_STYLE if dark else LIGHT_STYLE
