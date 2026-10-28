"""تست آفلاین درایور واقعی TsetmcClientTypeProvider (CR-20261029-001).

منشأ داده‌ها:
- ردیف‌های REAL_SNAPSHOT_ROWS: payload واقعی ClientTypeAll.aspx ضبط‌شدهٔ 2026-10-24
  (شواهد فاز ۰ فایل‌های 12/13 روی برنچ مستندات؛ CR-20261024-002) — بدون تغییر دستی.
- REAL_CLOSING_ROW: پاسخ واقعی GetClosingPriceDailyList فولاد برای dEven=20261021
  (فایل شواهد 10) — بدون تغییر دستی.
- ردیف‌های closing با برچسب SYNTHETIC: فقط برای ریاضی انتساب تاریخ در تست استفاده می‌شوند؛
  در مسیر اجرای production نیستند و نقض سیاست «فقط دادهٔ واقعی» نیستند.
- ردیف VIOLATING_ROW: ردیف سنتتیک نقض‌کنندهٔ اتحاد خرید/فروش (از تست قدیمی parser) —
  باید توسط گیت ساختاری رد شود.

هیچ تستی به شبکه وصل نمی‌شود؛ urlopen با فیکسچر در حافظه جایگزین می‌شود.
"""
from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import quote

import pytest

from arya.models.shareholders import ShareholderFlowMetrics
from arya.providers.shareholder_base import ShareholderProviderRegistry
from arya.providers.shareholders import tsetmc_client_type as tsetmc_module
from arya.providers.shareholders.tsetmc_client_type import TsetmcClientTypeProvider

# ── فیکسچر واقعی (پروونه‌بندی‌شده در شواهد فاز ۰) ──────────────────────────────

REAL_SNAPSHOT_ROWS = (
    "60333554838377493,0,1,0,900000,0,1,0,900000",
    "27797446447955609,30,2,7536356,1887096,27,1,1564136,7859316",
    "2019449432639594,75,1,795627,2257409,197,1,2962503,90533",
    "33903462343209810,0,1,0,5700000,0,1,0,5700000",
    "53809308236531169,11,3,2511640,1198380,27,1,3110020,600000",  # فولاد — کلید = کد قدیمی
)
REAL_SNAPSHOT_TEXT = ";".join(REAL_SNAPSHOT_ROWS)

VIOLATING_ROW = "46348559193224090,100,10,1000000,500000,80,20,400000,600000"  # خرید≠فروش — باید رد شود

FOOLAD_SEARCH = {
    "instrumentSearch": [
        {
            "lVal30": "فولاد مبارکه اصفهان",
            "lVal18AFC": "فولاد",
            "insCode": "46348559193224090",
            "insCode3": "53809308236531169",
            "cgrValCot": "B1",
            "flow": "1",
        }
    ]
}

# پاسخ واقعی بستهٔ فولاد 20261021 (فایل شواهد 10) — دست‌نخورده
REAL_CLOSING_ROW = {
    "priceChange": -110.0,
    "priceMin": 4210.0,
    "priceMax": 4340.0,
    "priceYesterday": 4340.0,
    "priceFirst": 4340.0,
    "last": False,
    "id": 0,
    "insCode": "46348559193224090",
    "dEven": 20261021,
    "hEven": 123002,
    "pClosing": 4220.0,
    "iClose": False,
    "yClose": True,
    "pDrCotVal": 4230.0,
    "zTotTran": 48279.0,
    "qTotTran5J": 4864252101.0,
    "qTotCap": 20519267355350.0,
}

# SYNTHETIC (برچسب‌دار) — حجم روز ۲۱ دقیقاً برابر حجم واقعی snapshot فولاد (۳٬۷۱۰٬۰۲۰) و VWAP=۲۱۰
ATTR_ROWS = [
    {"dEven": 20261020, "qTotTran5J": 2_000_000.0, "qTotCap": 400_000_000.0, "priceMin": 190.0, "priceMax": 210.0},
    {"dEven": 20261021, "qTotTran5J": 3_710_020.0, "qTotCap": 779_104_200.0, "priceMin": 200.0, "priceMax": 220.0},
]
AMBIGUOUS_ROWS = [
    {"dEven": 20261020, "qTotTran5J": 3_552_000.0, "qTotCap": 700_000_000.0, "priceMin": 190.0, "priceMax": 210.0},  # 4.45% < 5%
    {"dEven": 20261021, "qTotTran5J": 3_710_020.0, "qTotCap": 779_104_200.0, "priceMin": 200.0, "priceMax": 220.0},
]
OUT_OF_BAND_ROWS = [
    {"dEven": 20261021, "qTotTran5J": 3_710_020.0, "qTotCap": 779_104_200.0, "priceMin": 1000.0, "priceMax": 1100.0},
]


# ── زیرساخت فیک ────────────────────────────────────────────────────────────────

class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._payload


def make_fake_urlopen(routes):
    """routes: تابع url→bytes یا None (None یعنی خطای شبکه واقعی شبیه‌سازی شود)."""

    def fake_urlopen(request, timeout=0):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        payload = routes(url)
        if payload is None:
            raise URLError(f"no route in fake: {url}")
        return FakeResponse(payload)

    return fake_urlopen


def default_routes(
    snapshot_text: str = REAL_SNAPSHOT_TEXT,
    closing_rows: list = ATTR_ROWS,
    search_payload=FOOLAD_SEARCH,
):
    def route(url: str):
        if "GetInstrumentSearch" in url:
            if search_payload is None:
                return b"<html>proxy error</html>"
            return json.dumps(search_payload).encode("utf-8")
        if "ClientTypeAll.aspx" in url:
            return snapshot_text.encode("utf-8")
        if "GetClosingPriceDailyList" in url:
            return json.dumps({"closingPriceDaily": closing_rows}).encode("utf-8")
        return None

    return route


@pytest.fixture()
def provider(monkeypatch):
    def _build(routes, **kwargs):
        p = TsetmcClientTypeProvider(**kwargs)
        monkeypatch.setattr(tsetmc_module, "urlopen", make_fake_urlopen(routes))
        return p

    return _build


# ── تست‌ها: یکپارچگی قرارداد و مرز مدل ─────────────────────────────────────────

def test_registry_integration():
    """درایور روی همان Registry قرارداد فعلی ثبت شده باشد (کنار mock و client_type_all)."""
    from arya.providers.shareholder_base import ShareholderDataProvider
    from arya.providers.shareholders.client_type_all_provider import (
        ClientTypeAllProvider,  # noqa: F401 — ثبت در Registry هنگام import (یافتهٔ تست: بدون import، ثبت نمی‌شود)
    )

    created = ShareholderProviderRegistry.create("tsetmc_client_type")
    assert isinstance(created, ShareholderDataProvider)
    assert isinstance(created, TsetmcClientTypeProvider)
    assert {"mock", "client_type_all", "tsetmc_client_type"} <= set(
        ShareholderProviderRegistry._registry
    )


def test_usable_flow_returns_current_model(provider):
    p = provider(default_routes())
    m = p.fetch_shareholder_flow("فولاد")
    assert isinstance(m, ShareholderFlowMetrics)  # مرز Provider = مدل فعلی، نه dict
    assert m.ticker == "فولاد"
    assert m.data_quality == "usable"
    assert isinstance(m.shareholder_count_series, tuple)
    assert m.shareholder_count_series == ()  # نبود تاریخچه «صریح» است
    assert m.shareholder_count_change_pct is None
    assert m.legal_buy_share == round(1198380 / 3710020, 6)
    assert m.legal_net_buy_value == round((1198380 - 600000) * 210.0, 2)  # 598380×210
    assert m.individual_avg_buy_value == round(2511640 * 210.0 / 11, 2)
    assert m.individual_avg_sell_value == round(3110020 * 210.0 / 27, 2)
    assert any("snapshot_date=20261021" in n for n in m.notes)


# ── تست‌ها: نماد ناشناخته / پاسخ نامعتبر ───────────────────────────────────────

def test_unknown_symbol_missing(provider):
    p = provider(default_routes(search_payload={"instrumentSearch": []}))
    m = p.fetch_shareholder_flow("نماد-ناشناخته")
    assert isinstance(m, ShareholderFlowMetrics)
    assert m.data_quality == "missing"
    assert m.shareholder_count_series == ()
    assert m.legal_buy_share is None and m.legal_net_buy_value is None
    assert m.notes  # دلیل صریح


def test_invalid_search_response_missing(provider):
    p = provider(default_routes(search_payload=None))  # پاسخ HTML غیرJSON
    m = p.fetch_shareholder_flow("فولاد")
    assert m.data_quality == "missing"
    assert m.notes


def test_network_failure_missing(provider):
    p = provider(lambda url: None)  # همهٔ درخواست‌ها شکست می‌خورند
    m = p.fetch_shareholder_flow("فولاد")
    assert m.data_quality == "missing"
    assert m.notes


def test_snapshot_without_symbol_missing(provider):
    text = ";".join(REAL_SNAPSHOT_ROWS[:4])  # بدون ردیف فولاد
    p = provider(default_routes(snapshot_text=text))
    m = p.fetch_shareholder_flow("فولاد")
    assert m.data_quality == "missing"
    assert any("snapshot" in n for n in m.notes)


# ── تست‌ها: گیت سه‌لایهٔ انتساب تاریخ (ایراد ۴ مالک) ───────────────────────────

def test_ambiguous_volume_match_is_partial(provider):
    """دو روز در تلورانس ⇒ «مبهم» ⇒ partial با همهٔ متریک‌ها None (تطبیق اشتباه ممنوع)."""
    p = provider(default_routes(closing_rows=AMBIGUOUS_ROWS))
    m = p.fetch_shareholder_flow("فولاد")
    assert m.data_quality == "partial"
    assert m.legal_buy_share is None
    assert m.legal_net_buy_value is None
    assert m.individual_avg_buy_value is None
    assert m.shareholder_count_series == ()
    assert any("ambiguous_volume_match" in n for n in m.notes)


def test_vwap_outside_day_price_band_is_partial(provider):
    p = provider(default_routes(closing_rows=OUT_OF_BAND_ROWS))
    m = p.fetch_shareholder_flow("فولاد")
    assert m.data_quality == "partial"
    assert any("vwap_outside_day_price_band" in n for n in m.notes)


def test_real_closing_row_attribution_unit():
    """انتساب کاملاً واقعی: حجم واقعی روز بسته (4.86G) با ردیف بستهٔ واقعی فولاد."""
    p = TsetmcClientTypeProvider()
    att = p._attribute_snapshot_date(4864252101, [REAL_CLOSING_ROW])
    assert att.date == 20261021
    assert att.rejected_reason is None
    assert 4210.0 <= att.vwap <= 4340.0  # باند واقعی همان روز
    assert att.vwap == pytest.approx(20519267355350.0 / 4864252101.0)


def test_no_volume_match_is_partial(provider):
    rows = [{"dEven": 20261015, "qTotTran5J": 10_000_000.0, "qTotCap": 2.0e9, "priceMin": 190.0, "priceMax": 210.0}]
    p = provider(default_routes(closing_rows=rows))
    m = p.fetch_shareholder_flow("فولاد")
    assert m.data_quality == "partial"
    assert any("no_volume_match_within_tolerance" in n for n in m.notes)


def test_confirmed_date_mismatch_downgrades_to_partial(provider):
    """لایهٔ ۳: تاریخ منتسب با تأیید مستقل نمی‌خواند ⇒ partial؛ سازگار ⇒ usable."""
    p = provider(default_routes())
    ok = p.fetch_shareholder_flow("فولاد", confirmed_date=20261021)
    assert ok.data_quality == "usable"
    bad = p.fetch_shareholder_flow("فولاد", confirmed_date=20261020)
    assert bad.data_quality == "partial"
    assert any("تأییدشدهٔ مستقل" in n for n in bad.notes)


# ── تست‌ها: تأیید مستقل چند-نمادی (confirm_snapshot_date) ─────────────────────

SYNTH_A_SEARCH = {"instrumentSearch": [{"lVal18AFC": "تستآ", "insCode": "11111111111111111", "insCode3": "11111111111111110"}]}
SYNTH_B_SEARCH = {"instrumentSearch": [{"lVal18AFC": "تستب", "insCode": "22222222222222222", "insCode3": "22222222222222220"}]}
# هویت‌های SYNTHETIC (برچسب‌دار) فقط برای plumbing توافق چند-نمادی؛ کدهای واقعی فقط فولاد است.
SYNTH_SNAPSHOT_ROWS = (
    "11111111111111110,5,1,2000000,1500000,4,1,2000000,1500000",  # مجموع خرید = مجموع فروش = 3500000
    "22222222222222220,6,1,3000000,1000000,5,1,3000000,1000000",  # مجموع خرید = مجموع فروش = 4000000
)


def _confirm_routes(snap_text: str, ticker_closings: dict[str, list[dict]]):
    """روتر فیک برای confirm_snapshot_date؛ هر نماد تاریخچهٔ بستهٔ خودش را دارد."""
    closing_by_code = {
        "11111111111111111": ticker_closings.get("تستآ", []),
        "22222222222222222": ticker_closings.get("تستب", []),
    }

    def route(url: str):
        if "GetInstrumentSearch" in url:
            if quote("فولاد") in url:
                return json.dumps(FOOLAD_SEARCH).encode("utf-8")
            if quote("تستآ") in url:
                return json.dumps(SYNTH_A_SEARCH).encode("utf-8")
            if quote("تستب") in url:
                return json.dumps(SYNTH_B_SEARCH).encode("utf-8")
            return None
        if "ClientTypeAll.aspx" in url:
            return snap_text.encode("utf-8")
        if "GetClosingPriceDailyList" in url:
            for code, rows in closing_by_code.items():
                if code in url:
                    return json.dumps({"closingPriceDaily": rows}).encode("utf-8")
            if "46348559193224090" in url:
                return json.dumps({"closingPriceDaily": ATTR_ROWS}).encode("utf-8")
            return None
        return None

    return route


def test_confirm_snapshot_date_agreement(provider):
    """دو نماد مستقل هر دو روز ۲۱ را می‌یابند ⇒ توافق کامل؛ agreed_date برقرار."""
    snap = ";".join(REAL_SNAPSHOT_ROWS + (SYNTH_SNAPSHOT_ROWS[0],))
    routes = _confirm_routes(
        snap,
        {"تستآ": [{"dEven": 20261021, "qTotTran5J": 3500000.0, "qTotCap": 350000000.0, "priceMin": 90.0, "priceMax": 110.0}]},
    )
    p = provider(routes)
    out = p.confirm_snapshot_date(("فولاد", "تستآ"), days=5)
    assert out["agreed_date"] == 20261021
    assert out["agreement_ratio"] == 1.0
    assert out["per_ticker"]["فولاد"]["verdict"] == "attributed"
    assert out["per_ticker"]["تستآ"]["date"] == 20261021


def test_confirm_snapshot_date_disagreement_blocks(provider):
    """تطبیق اشتباه شبیه‌سازی‌شده: یک نماد به روز دیگری منتسب می‌شود ⇒ توافق کافی نیست ⇒ None.

    این دقیقاً همان ریسک ایراد ۴ مالک است: حجمِ هر نماد با روزِ اشتباهی می‌خورد و
    بدون توافق چند-نمادی، انتساب تک-نمادی قابل اعتماد نیست.
    """
    snap = ";".join(REAL_SNAPSHOT_ROWS + (SYNTH_SNAPSHOT_ROWS[1],))
    routes = _confirm_routes(
        snap,
        {"تستب": [{"dEven": 20261018, "qTotTran5J": 4000000.0, "qTotCap": 200000000.0, "priceMin": 45.0, "priceMax": 55.0}]},
    )
    p = provider(routes)
    out = p.confirm_snapshot_date(("فولاد", "تستب", "ناموجود"), days=5)
    # فولاد→20261021، تستب→20261018 (تطبیق متفاوت)، ناموجود→missing ⇒ نسبت 1/3 < 0.6
    assert out["agreed_date"] is None
    assert out["agreement_ratio"] == pytest.approx(1 / 3, abs=1e-3)
    assert out["per_ticker"]["تستب"]["date"] == 20261018


# ── تست‌ها: گیت ساختاری snapshot ───────────────────────────────────────────────

def test_invariant_gate_rejects_violating_row(provider):
    text = ";".join(list(REAL_SNAPSHOT_ROWS) + [VIOLATING_ROW])
    p = provider(default_routes(snapshot_text=text))
    rows, rejected = p.fetch_market_snapshot()
    assert rejected == 1
    assert "46348559193224090" not in rows
    assert "53809308236531169" in rows  # ردیف واقعی فولاد سالم مانده است


def test_inspect_snapshot_has_no_derived_metrics(provider):
    p = provider(default_routes())
    out = p.inspect_snapshot("فولاد")
    assert out["matched_by"] == "old_ins_code"
    assert out["row"]["total_buy_volume"] == 3_710_020
    assert out["attribution"]["verdict"] == "attributed"
    assert "individual_avg_buy_value" not in out  # هیچ متریک مشتق‌شده‌ای در مسیر inspect
