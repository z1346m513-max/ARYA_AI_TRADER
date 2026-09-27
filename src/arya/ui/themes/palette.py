"""رنگ‌ها و پوستهٔ تیرهٔ ARYA AI Trader برای رابط فارسی/راست‌به‌چپ."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


COLORS = {
    "canvas": "#0B1220",
    "sidebar": "#0D1728",
    "panel": "#121E31",
    "panel_alt": "#17263B",
    "border": "#263850",
    "text": "#EAF1F8",
    "muted": "#9AACBF",
    "subtle": "#6F849C",
    "teal": "#32C6B0",
    "teal_soft": "#173D40",
    "blue": "#6C9EFF",
    "violet": "#A18BFF",
    "green": "#43D19E",
    "red": "#FF7185",
    "amber": "#F5BF62",
}


def apply_theme(app: QApplication) -> None:
    """Apply a coherent high-contrast dark palette without changing global OS settings."""
    app.setStyleSheet(f"""
        QWidget {{
            color: {COLORS['text']};
            font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
            font-size: 13px;
        }}
        QMainWindow, QWidget#appRoot {{ background: {COLORS['canvas']}; }}
        QFrame#sidebar {{ background: {COLORS['sidebar']}; border: 1px solid {COLORS['border']}; border-radius: 18px; }}
        QFrame#panel {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 16px; }}
        QFrame#metricPanel {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 15px; }}
        QLabel#muted {{ color: {COLORS['muted']}; }}
        QLabel#subtle {{ color: {COLORS['subtle']}; }}
        QLabel#brandMark {{ color: {COLORS['canvas']}; background: {COLORS['teal']}; border-radius: 12px; font-size: 18px; font-weight: 900; }}
        QPushButton {{ background: {COLORS['panel_alt']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 9px 13px; }}
        QPushButton:hover {{ background: #1D304A; border-color: {COLORS['teal']}; }}
        QPushButton#primaryButton {{ background: {COLORS['teal']}; color: #071A1A; border: 0; font-weight: 700; }}
        QPushButton#primaryButton:hover {{ background: #55D7C4; }}
        QPushButton#navActive {{ background: {COLORS['teal_soft']}; color: {COLORS['teal']}; border: 1px solid #286765; font-weight: 700; text-align: right; }}
        QPushButton#navInactive {{ background: transparent; color: {COLORS['muted']}; border: 0; text-align: right; }}
        QPushButton#navInactive:hover {{ background: {COLORS['panel_alt']}; color: {COLORS['text']}; }}
        QLineEdit, QComboBox {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 9px 12px; min-height: 20px; }}
        QLineEdit:focus, QComboBox:focus {{ border-color: {COLORS['teal']}; }}
        QTableWidget {{ background: transparent; alternate-background-color: {COLORS['panel_alt']}; border: 0; gridline-color: {COLORS['border']}; selection-background-color: {COLORS['teal_soft']}; }}
        QHeaderView::section {{ background: {COLORS['panel_alt']}; color: {COLORS['muted']}; border: 0; padding: 8px; font-weight: 600; }}
        QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {COLORS['border']}; border-radius: 4px; min-height: 24px; }}
        QToolTip {{ background: {COLORS['panel_alt']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; padding: 5px; }}
    """)
