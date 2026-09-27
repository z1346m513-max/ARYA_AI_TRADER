"""Persian RTL desktop dashboard for ARYA AI Trader."""

from __future__ import annotations

from typing import Any, Optional

import copy

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from arya.app.bootstrap import AryaApp
from arya.models.analysis_result import Recommendation
from arya.ui.i18n import (
    translate_action,
    translate_alert,
    translate_market,
    translate_risk,
)
from arya.ui.rtl import normalize_ticker


class AnalysisWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, settings, ticker: str, market: str, timeframe: str):
        super().__init__()
        self.settings = settings
        self.ticker = ticker
        self.market = market
        self.timeframe = timeframe

    @Slot()
    def run(self) -> None:
        app_service = None
        try:
            # SQLite connections are thread-bound. Construct AryaApp inside
            # this worker thread instead of sharing GUI-thread connections.
            app_service = AryaApp(settings=self.settings)
            result = app_service.analyze_symbol(
                self.ticker,
                market=self.market,
                timeframe=self.timeframe,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            if app_service is not None:
                try:
                    app_service.history_cache.close()
                finally:
                    app_service.store.close()


class MainWindow(QMainWindow):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.language = settings.app.get("app", {}).get("language", "fa")

        self._thread: Optional[QThread] = None
        self._worker: Optional[AnalysisWorker] = None

        self.setWindowTitle("ARYA AI Trader — تحلیل‌گر بازار")
        size = settings.ui.get("windows", {}).get("main", {})
        self.resize(int(size.get("width", 1400)), int(size.get("height", 900)))
        self.setMinimumSize(1000, 700)

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel("آریا — تحلیل‌گر هوشمند بازار")
        title.setObjectName("title")
        subtitle = QLabel("تحلیل تکنیکال با داده واقعی بورس ایران و TSETMC")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        search_box = QGroupBox("انتخاب نماد و پارامترهای تحلیل")
        search_layout = QGridLayout(search_box)
        search_layout.setHorizontalSpacing(12)
        search_layout.setVerticalSpacing(10)

        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("نماد را وارد کنید؛ مثال: فملی")
        self.ticker_input.setClearButtonEnabled(True)
        self.ticker_input.setInputMethodHints(Qt.InputMethodHint.ImhNone)
        self.ticker_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.ticker_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.market_combo = QComboBox()
        self.market_combo.addItem("بورس ایران", "stock")
        self.market_combo.addItem("ارز دیجیتال", "crypto")
        self.market_combo.addItem("فارکس", "forex")
        self.market_combo.setCurrentIndex(0)

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItem("روزانه", "1d")

        self.analyze_button = QPushButton("شروع تحلیل")
        self.analyze_button.setDefault(True)
        self.analyze_button.clicked.connect(self._start_analysis)
        self.ticker_input.returnPressed.connect(self._start_analysis)

        search_layout.addWidget(QLabel("نماد:"), 0, 0)
        search_layout.addWidget(self.ticker_input, 0, 1)
        search_layout.addWidget(QLabel("بازار:"), 0, 2)
        search_layout.addWidget(self.market_combo, 0, 3)
        search_layout.addWidget(QLabel("تایم‌فریم:"), 0, 4)
        search_layout.addWidget(self.timeframe_combo, 0, 5)
        search_layout.addWidget(self.analyze_button, 0, 6)

        root.addWidget(search_box)

        settings_box = QGroupBox("تنظیمات قابل تغییر تحلیل")
        settings_layout = QFormLayout(settings_box)

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("متعادل", "balanced")
        self.profile_combo.addItem("محافظه‌کار", "conservative")
        self.profile_combo.addItem("مومنتوم", "momentum")
        self.profile_combo.addItem("دنبال‌کننده روند", "trend_following")
        self.profile_combo.currentIndexChanged.connect(self._load_profile_defaults)

        self.history_limit = self._spin(50, 1000, 200, 50)
        self.sma_period = self._spin(2, 500, 20, 1)
        self.ema_period = self._spin(2, 500, 50, 1)
        self.rsi_period = self._spin(2, 200, 14, 1)
        self.rsi_overbought = self._spin(50, 100, 70, 1)
        self.rsi_oversold = self._spin(0, 50, 30, 1)
        self.macd_fast = self._spin(2, 100, 12, 1)
        self.macd_slow = self._spin(3, 200, 26, 1)
        self.macd_signal = self._spin(2, 100, 9, 1)
        self.bb_period = self._spin(2, 500, 20, 1)
        self.bb_std = self._double_spin(0.5, 5.0, 2.0, 0.1)
        self.buy_threshold = self._double_spin(0.01, 1.0, 0.25, 0.01)
        self.sell_threshold = self._double_spin(-1.0, -0.01, -0.25, 0.01)

        settings_layout.addRow("پروفایل:", self.profile_combo)
        settings_layout.addRow("تعداد کندل تاریخچه:", self.history_limit)

        ma_row = QHBoxLayout()
        ma_row.addWidget(QLabel("SMA"))
        ma_row.addWidget(self.sma_period)
        ma_row.addWidget(QLabel("EMA"))
        ma_row.addWidget(self.ema_period)
        settings_layout.addRow("میانگین‌ها:", ma_row)

        rsi_row = QHBoxLayout()
        rsi_row.addWidget(QLabel("دوره"))
        rsi_row.addWidget(self.rsi_period)
        rsi_row.addWidget(QLabel("اشباع خرید"))
        rsi_row.addWidget(self.rsi_overbought)
        rsi_row.addWidget(QLabel("اشباع فروش"))
        rsi_row.addWidget(self.rsi_oversold)
        settings_layout.addRow("RSI:", rsi_row)

        macd_row = QHBoxLayout()
        macd_row.addWidget(QLabel("سریع"))
        macd_row.addWidget(self.macd_fast)
        macd_row.addWidget(QLabel("کند"))
        macd_row.addWidget(self.macd_slow)
        macd_row.addWidget(QLabel("سیگنال"))
        macd_row.addWidget(self.macd_signal)
        settings_layout.addRow("MACD:", macd_row)

        bb_row = QHBoxLayout()
        bb_row.addWidget(QLabel("دوره"))
        bb_row.addWidget(self.bb_period)
        bb_row.addWidget(QLabel("انحراف معیار"))
        bb_row.addWidget(self.bb_std)
        settings_layout.addRow("بولینگر:", bb_row)

        decision_row = QHBoxLayout()
        decision_row.addWidget(QLabel("آستانه خرید"))
        decision_row.addWidget(self.buy_threshold)
        decision_row.addWidget(QLabel("آستانه فروش"))
        decision_row.addWidget(self.sell_threshold)
        settings_layout.addRow("تصمیم:", decision_row)

        root.addWidget(settings_box)
        self._load_profile_defaults()

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        root.addWidget(self.progress)

        self.summary_box = QGroupBox("نتیجه تحلیل")
        summary = QGridLayout(self.summary_box)

        self.symbol_label = QLabel("—")
        self.action_label = QLabel("—")
        self.score_label = QLabel("—")
        self.confidence_label = QLabel("—")
        self.trend_label = QLabel("—")
        self.liquidity_label = QLabel("—")

        fields = [
            ("نماد", self.symbol_label),
            ("وضعیت", self.action_label),
            ("امتیاز کلی", self.score_label),
            ("اطمینان", self.confidence_label),
            ("کیفیت روند", self.trend_label),
            ("نقدشوندگی", self.liquidity_label),
        ]
        for index, (label, value) in enumerate(fields):
            row, col = divmod(index, 3)
            summary.addWidget(QLabel(label), row * 2, col)
            summary.addWidget(value, row * 2 + 1, col)

        root.addWidget(self.summary_box)

        self.risk_box = QGroupBox("ارزیابی ریسک")
        risk = QGridLayout(self.risk_box)
        self.risk_level = QLabel("—")
        self.risk_score = QLabel("—")
        self.position = QLabel("—")
        self.stop_loss = QLabel("—")
        risk_fields = [
            ("سطح ریسک", self.risk_level),
            ("امتیاز ریسک", self.risk_score),
            ("حداکثر پوزیشن", self.position),
            ("حد ضرر پیشنهادی", self.stop_loss),
        ]
        for col, (label, value) in enumerate(risk_fields):
            risk.addWidget(QLabel(label), 0, col)
            risk.addWidget(value, 1, col)

        root.addWidget(self.risk_box)

        content = QHBoxLayout()
        reasons_box = QGroupBox("دلایل تحلیل")
        reasons_layout = QVBoxLayout(reasons_box)
        self.reasons_table = QTableWidget(0, 1)
        self.reasons_table.setHorizontalHeaderLabels(["شرح"])
        self.reasons_table.horizontalHeader().setStretchLastSection(True)
        self.reasons_table.verticalHeader().setVisible(False)
        self.reasons_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        reasons_layout.addWidget(self.reasons_table)

        indicators_box = QGroupBox("هشدارها و نشانه‌ها")
        indicators_layout = QVBoxLayout(indicators_box)
        self.alerts_table = QTableWidget(0, 1)
        self.alerts_table.setHorizontalHeaderLabels(["شرح"])
        self.alerts_table.horizontalHeader().setStretchLastSection(True)
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        indicators_layout.addWidget(self.alerts_table)

        content.addWidget(reasons_box, 1)
        content.addWidget(indicators_box, 1)
        root.addLayout(content, 1)

        status_bar = self.statusBar()
        status_bar.showMessage("آماده")
        self.setCentralWidget(central)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                font-size: 12pt;
            }
            QLabel#title {
                font-size: 24pt;
                font-weight: 700;
            }
            QLabel#subtitle {
                color: #6B7280;
                padding-bottom: 4px;
            }
            QGroupBox {
                font-weight: 700;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 14px;
                padding: 0 6px;
            }
            QLineEdit, QComboBox, QPushButton {
                min-height: 40px;
                border-radius: 7px;
                padding: 4px 10px;
            }
            QPushButton {
                font-weight: 700;
            }
            QTableWidget {
                border: 1px solid #D1D5DB;
                border-radius: 8px;
            }
            """
        )

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int, step: int) -> QSpinBox:
        box = QSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setSingleStep(step)
        return box

    @staticmethod
    def _double_spin(minimum: float, maximum: float, value: float, step: float) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setValue(value)
        box.setSingleStep(step)
        box.setDecimals(2)
        return box

    def _load_profile_defaults(self) -> None:
        profile_name = self.profile_combo.currentData()
        try:
            profile = self.settings.analysis_profile(profile_name)
        except Exception:
            return
        indicators = profile.get("indicators", {})
        trend = indicators.get("trend", {})
        momentum = indicators.get("momentum", {})
        volatility = indicators.get("volatility", {})

        self.history_limit.setValue(int(profile.get("history_limit", 200)))
        self.sma_period.setValue(int(trend.get("sma", {}).get("params", {}).get("period", 20)))
        self.ema_period.setValue(int(trend.get("ema", {}).get("params", {}).get("period", 50)))
        self.rsi_period.setValue(int(momentum.get("rsi", {}).get("params", {}).get("period", 14)))
        self.rsi_overbought.setValue(int(momentum.get("rsi", {}).get("params", {}).get("overbought", 70)))
        self.rsi_oversold.setValue(int(momentum.get("rsi", {}).get("params", {}).get("oversold", 30)))
        self.macd_fast.setValue(int(momentum.get("macd", {}).get("params", {}).get("fast", 12)))
        self.macd_slow.setValue(int(momentum.get("macd", {}).get("params", {}).get("slow", 26)))
        self.macd_signal.setValue(int(momentum.get("macd", {}).get("params", {}).get("signal", 9)))
        self.bb_period.setValue(int(volatility.get("bollinger", {}).get("params", {}).get("period", 20)))
        self.bb_std.setValue(float(volatility.get("bollinger", {}).get("params", {}).get("std_dev", 2)))
        decision = profile.get("decision", {})
        self.buy_threshold.setValue(float(decision.get("buy_threshold", 0.25)))
        self.sell_threshold.setValue(float(decision.get("sell_threshold", -0.25)))

    def _analysis_settings(self):
        profile_name = self.profile_combo.currentData()
        indicator_overrides: dict[str, Any] = copy.deepcopy(self.settings.analysis_profile(profile_name).get("indicators", {}))
        for group, name, params in [
            ("trend", "sma", {"period": self.sma_period.value()}),
            ("trend", "ema", {"period": self.ema_period.value()}),
            (
                "momentum",
                "rsi",
                {
                    "period": self.rsi_period.value(),
                    "overbought": self.rsi_overbought.value(),
                    "oversold": self.rsi_oversold.value(),
                },
            ),
            (
                "momentum",
                "macd",
                {
                    "fast": self.macd_fast.value(),
                    "slow": self.macd_slow.value(),
                    "signal": self.macd_signal.value(),
                },
            ),
            (
                "volatility",
                "bollinger",
                {"period": self.bb_period.value(), "std_dev": self.bb_std.value()},
            ),
        ]:
            indicator_overrides.setdefault(group, {}).setdefault(name, {})["params"] = params

        return self.settings.for_analysis(
            profile_name=profile_name,
            indicator_overrides=indicator_overrides,
            decision_overrides={
                "buy_threshold": self.buy_threshold.value(),
                "sell_threshold": self.sell_threshold.value(),
            },
            history_limit=self.history_limit.value(),
        )

    def _start_analysis(self) -> None:
        if self._thread is not None:
            return

        ticker = normalize_ticker(self.ticker_input.text())
        if not ticker:
            QMessageBox.warning(self, "ورودی نامعتبر", "لطفاً نماد را وارد کنید.")
            self.ticker_input.setFocus()
            return

        market = self.market_combo.currentData()
        timeframe = self.timeframe_combo.currentData()
        analysis_settings = self._analysis_settings()

        self.analyze_button.setEnabled(False)
        self.progress.setVisible(True)
        self.statusBar().showMessage("در حال دریافت داده و تحلیل…")

        self._thread = QThread(self)
        self._worker = AnalysisWorker(
            analysis_settings,
            ticker,
            market,
            timeframe,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_result)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(self._finish_thread)
        self._worker.failed.connect(self._finish_thread)
        self._thread.finished.connect(self._clear_thread)
        self._thread.start()

    @Slot(object)
    def _on_result(self, rec: Recommendation) -> None:
        symbol, _, market_code = rec.symbol.partition("@")
        self.symbol_label.setText(
            f"{symbol} — {translate_market(market_code, self.language)}"
            if market_code
            else symbol
        )
        self.action_label.setText(translate_action(rec.action, self.language))
        self.score_label.setText(f"{float(rec.overall_score):+.2f}")
        self.confidence_label.setText(f"{rec.confidence:.0%}")
        self.trend_label.setText(f"{rec.trend_quality:.0%}")
        self.liquidity_label.setText(f"{float(rec.liquidity_strength):.0%}")

        if rec.risk:
            self.risk_level.setText(translate_risk(rec.risk.risk_level, self.language))
            self.risk_score.setText(f"{float(rec.risk.risk_score):.2f}")
            self.position.setText(f"{rec.risk.max_position_size_pct:.1f}%")
            self.stop_loss.setText(
                f"{rec.risk.stop_loss_pct:.1f}%"
                if rec.risk.stop_loss_pct is not None
                else "—"
            )

        self.reasons_table.setRowCount(0)
        for reason in rec.reasons:
            row = self.reasons_table.rowCount()
            self.reasons_table.insertRow(row)
            self.reasons_table.setItem(row, 0, QTableWidgetItem(reason))

        alerts = []
        for section in rec.section_scores:
            for alert in (section.details or {}).get("alerts", []):
                alerts.append(translate_alert(alert, self.language))
        self.alerts_table.setRowCount(0)
        for alert in alerts:
            row = self.alerts_table.rowCount()
            self.alerts_table.insertRow(row)
            self.alerts_table.setItem(row, 0, QTableWidgetItem(alert))

        self.statusBar().showMessage("تحلیل با موفقیت انجام شد")

    @Slot(str)
    def _on_error(self, message: str) -> None:
        self.statusBar().showMessage("اجرای تحلیل ناموفق بود")
        QMessageBox.critical(
            self,
            "خطا در تحلیل",
            f"دریافت داده یا تحلیل با خطا مواجه شد:\n\n{message}",
        )

    @Slot()
    def _finish_thread(self) -> None:
        if self._thread is not None:
            self._thread.quit()

    @Slot()
    def _clear_thread(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        self._thread = None
        self._worker = None
        self.analyze_button.setEnabled(True)
        self.progress.setVisible(False)

    def closeEvent(self, event) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(5000)
        event.accept()
