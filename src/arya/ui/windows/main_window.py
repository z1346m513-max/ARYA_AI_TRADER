"""داشبورد اولیهٔ PySide6؛ بدون نمایش دادهٔ بازارِ ساختگی به‌عنوان دادهٔ زنده."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from arya.ui.themes.palette import COLORS


class EmptyChart(QWidget):
    """Chart placeholder until a real market-data provider is configured."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(235)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName("نمودار بازار؛ در انتظار اتصال منبع داده")

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 8, -8, -8)
        grid_pen = QPen(QColor(COLORS["border"]))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        for row in range(1, 5):
            y = rect.top() + rect.height() * row / 5
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
        painter.setPen(QColor(COLORS["teal"]))
        painter.setBrush(QColor(COLORS["teal_soft"]))
        painter.drawRoundedRect(rect.left() + 10, rect.top() + 12, 112, 26, 8, 8)
        painter.setPen(QColor(COLORS["teal"]))
        painter.setFont(QFont("Vazirmatn", 9, QFont.Weight.DemiBold))
        painter.drawText(rect.left() + 19, rect.top() + 30, "منبع متصل نیست")
        painter.setPen(QColor(COLORS["muted"]))
        painter.setFont(QFont("Vazirmatn", 12))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "پس از پیکربندی Provider مجاز، نمودار قیمت اینجا نمایش داده می‌شود")


class MainWindow(QMainWindow):
    """A polished, RTL dashboard shell ready to receive Recommendation/market data."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ARYA AI Trader | میز تحلیل بازار")
        self.setMinimumSize(1180, 760)
        self.resize(1440, 900)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _panel(self, title: str, subtitle: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(heading)
        if subtitle:
            hint = QLabel(subtitle)
            hint.setObjectName("muted")
            hint.setWordWrap(True)
            layout.addWidget(hint)
        return panel, layout

    def _metric(self, title: str, detail: str, accent: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("metricPanel")
        panel.setMinimumHeight(112)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("muted")
        value = QLabel("—")
        value.setStyleSheet(f"font-size: 25px; font-weight: 800; color: {accent};")
        note = QLabel(detail)
        note.setObjectName("subtle")
        note.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addWidget(note)
        return panel

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(18, 18, 18, 18)
        shell.setSpacing(18)

        # With RTL direction, the first column is the right-hand navigation rail.
        shell.addWidget(self._build_sidebar())
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        shell.addWidget(content, 1)

        content_layout.addWidget(self._build_header())
        content_layout.addWidget(self._build_status())
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        tiles = [
            ("شاخص منتخب", "پس از اتصال منبع قیمت", COLORS["teal"]),
            ("نمادهای پایش‌شده", "واچ‌لیست هنوز تنظیم نشده", COLORS["blue"]),
            ("وضعیت تحلیل", "موتور آماده؛ دادهٔ واقعی لازم است", COLORS["violet"]),
            ("آخرین دریافت", "زمان دریافت پس از اتصال ثبت می‌شود", COLORS["amber"]),
        ]
        for col, item in enumerate(tiles):
            metrics.addWidget(self._metric(*item), 0, col)
        content_layout.addLayout(metrics)

        main_row = QHBoxLayout()
        main_row.setSpacing(14)
        chart_panel, chart_layout = self._panel("نمای بازار", "نمودار فقط از دادهٔ دارای منبع و زمان دریافت تغذیه می‌شود.")
        chart_layout.addWidget(EmptyChart())
        main_row.addWidget(chart_panel, 7)

        watch_panel, watch_layout = self._panel("واچ‌لیست", "پس از انتخاب نمادها، قیمت و تغییرات با منبع/زمان به‌روزرسانی نمایش داده می‌شوند.")
        empty = QLabel("هنوز نمادی به واچ‌لیست افزوده نشده است")
        empty.setObjectName("muted")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setMinimumHeight(120)
        watch_layout.addStretch(1)
        watch_layout.addWidget(empty)
        add_symbol = QPushButton("افزودن نماد")
        add_symbol.setObjectName("primaryButton")
        add_symbol.setEnabled(False)
        add_symbol.setToolTip("پس از پیاده‌سازی Watchlist فعال می‌شود")
        watch_layout.addWidget(add_symbol)
        watch_layout.addStretch(1)
        main_row.addWidget(watch_panel, 4)
        content_layout.addLayout(main_row, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(14)
        codal_panel, codal_layout = self._panel("تازه‌ترین اطلاعیه‌های کدال", "اطلاعیه‌ها پس از اتصال منبع مجاز و همگام‌سازی نمایش داده می‌شوند.")
        codal_placeholder = QLabel("فعلاً داده‌ای از کدال دریافت نشده است")
        codal_placeholder.setObjectName("muted")
        codal_placeholder.setMinimumHeight(65)
        codal_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        codal_layout.addWidget(codal_placeholder)
        bottom.addWidget(codal_panel, 3)

        decision_panel, decision_layout = self._panel("خلاصهٔ تحلیل", "امتیاز بدون دادهٔ تازه و قابل‌ردیابی تولید نمی‌شود.")
        decision_placeholder = QLabel("در انتظار دادهٔ تکنیکال و بنیادی")
        decision_placeholder.setObjectName("muted")
        decision_placeholder.setMinimumHeight(65)
        decision_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        decision_layout.addWidget(decision_placeholder)
        bottom.addWidget(decision_panel, 2)
        content_layout.addLayout(bottom)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 18, 15, 18)
        layout.setSpacing(10)

        brand_row = QHBoxLayout()
        mark = QLabel("A")
        mark.setObjectName("brandMark")
        mark.setFixedSize(40, 40)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand = QVBoxLayout()
        name = QLabel("ARYA")
        name.setStyleSheet("font-size: 18px; font-weight: 900; letter-spacing: 1px;")
        caption = QLabel("AI TRADER")
        caption.setObjectName("subtle")
        caption.setStyleSheet("font-size: 9px; letter-spacing: 2px;")
        brand.addWidget(name)
        brand.addWidget(caption)
        brand_row.addWidget(mark)
        brand_row.addLayout(brand, 1)
        layout.addLayout(brand_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {COLORS['border']}; margin-top: 10px; margin-bottom: 8px;")
        layout.addWidget(divider)
        for text, active in [
            ("نمای کلی", True),
            ("واچ‌لیست", False),
            ("غربالگر نمادها", False),
            ("تحلیل بنیادی و کدال", False),
            ("مدیریت پرتفوی", False),
        ]:
            button = QPushButton(text)
            button.setObjectName("navActive" if active else "navInactive")
            button.setMinimumHeight(42)
            button.setEnabled(active)
            if not active:
                button.setToolTip("در نقشه‌راه رابط گرافیکی قرار دارد")
            layout.addWidget(button)
        layout.addStretch(1)

        help_label = QLabel("دادهٔ مالی با زمان و منبع")
        help_label.setObjectName("muted")
        help_label.setWordWrap(True)
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setStyleSheet(f"background: {COLORS['panel_alt']}; border-radius: 12px; padding: 12px;")
        layout.addWidget(help_label)
        version = QLabel("نسخهٔ نمایشی رابط")
        version.setObjectName("subtle")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        return sidebar

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        title_block = QVBoxLayout()
        title = QLabel("میز تحلیل بازار")
        title.setStyleSheet("font-size: 23px; font-weight: 800;")
        subtitle = QLabel("بازار، شواهد و ریسک در یک نمای روشن و قابل‌ردیابی")
        subtitle.setObjectName("muted")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        layout.addLayout(title_block, 1)

        self.symbol_search = QLineEdit()
        self.symbol_search.setPlaceholderText("جست‌وجوی نماد…")
        self.symbol_search.setMaximumWidth(210)
        self.symbol_search.setClearButtonEnabled(True)
        self.symbol_search.setEnabled(False)
        self.market_select = QComboBox()
        self.market_select.addItems(["بورس ایران", "رمزارز", "فارکس"])
        self.market_select.setMaximumWidth(150)
        self.market_select.setEnabled(False)
        self.refresh_button = QPushButton("وضعیت منابع")
        self.refresh_button.clicked.connect(self._show_source_status)
        layout.addWidget(self.symbol_search)
        layout.addWidget(self.market_select)
        layout.addWidget(self.refresh_button)
        return header

    def _build_status(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("panel")
        row = QHBoxLayout(bar)
        row.setContentsMargins(14, 9, 14, 9)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['amber']}; font-size: 12px;")
        self.status_label = QLabel("حالت آماده‌سازی: Provider آنلاین پیکربندی نشده؛ قیمت زنده در این نما نمایش داده نمی‌شود.")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        row.addWidget(dot)
        row.addWidget(self.status_label, 1)
        return bar

    def _show_source_status(self) -> None:
        self.status_label.setText("Mock فعلی فقط برای آزمون است؛ برای دادهٔ زنده باید منبع مجاز و کلید دسترسی در تنظیمات اجرا شود.")
