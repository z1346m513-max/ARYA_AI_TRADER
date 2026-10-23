"""تست درایور واقعی حقیقی/حقوقی TSETMC (CR-20261024-002).

قاعدهٔ فیکسچر:
- ردیف‌های snapshot، پاسخ جست‌وجو و تاریخچهٔ بستهٔ فولاد، همگی «دادهٔ واقعی ضبط‌شده»
  در docs/sources/evidence/2026-10-24/ هستند (فایل‌های 10، 11 و 13) — بدون تغییر دستی.
- تنها استثنا: در دو تست، یک ردیف closing با برچسب صریح «سنتتیکِ فقط-تست» افزوده می‌شود
  تا مسیر ریاضی انتساب تاریخ پوشش داده شود؛ مسیر اجرای محصول هرگز از دادهٔ سنتتیک استفاده نمی‌کند.
"""
import json
from urllib.parse import quote

import pytest

from arya.providers.shareholders import (
    FLOW_KEYS,
    ShareholderDataProviderError,
    ShareholderProviderRegistry,
    TsetmcClientTypeProvider,
)

# ─────────────── دادهٔ واقعی ضبط‌شده (evidence/2026-10-24) ───────────────

# فایل 13 — snapshot واقعی؛ در دادهٔ اصلی یک خط با جداکنندهٔ ";" است
REAL_SNAPSHOT_TEXT = (
    "971068957336171,1,1,100,44456,2,1,44456,100;"
    "25079426576214829,268,3,29108088,10969046,594,6,28716606,11360528;"
    "41625340598198551,26,0,177623,0,2,0,177623,0;"
    "53809308236531169,11,3,2511640,1198380,27,1,3110020,600000"
)

REAL_SNAPSHOT_WITHOUT_FOOLAD = (
    "971068957336171,1,1,100,44456,2,1,44456,100;"
    "25079426576214829,268,3,29108088,10969046,594,6,28716606,11360528;"
    "41625340598198551,26,0,177623,0,2,0,177623,0"
)

# فایل 11 — ردیف واقعی فولاد از GetInstrumentSearch (کپی بدون تغییر)
REAL_FOOLAD_SEARCH_JSON = json.dumps(
    {
        "instrumentSearch": [
            {
                "insCode2": "61934586397353104",
                "insCode3": "53809308236531169",
                "insCode4": "61318276340211749",
                "insCode": "46348559193224090",
                "lVal30": "فولاد مباركه اصفهان",
                "lVal18AFC": "فولاد",
                "flow": 1,
                "cIsin": None,
                "zTitad": 0.0,
                "baseVol": 0,
                "instrumentID": None,
                "cgrValCot": "N1",
                "cComVal": None,
                "lastDate": 1,
                "sourceID": 1,
                "flowTitle": "بازار بورس",
                "cgrValCotTitle": "",
            }
        ]
    },
    ensure_ascii=False,
)

# فایل 10 — تاریخچهٔ بستهٔ واقعی فولاد (۵ روز، بدون تغییر)
REAL_CLOSING_JSON = json.dumps(
    {
        "closingPriceDaily": [
            {"priceChange": -110.00, "priceMin": 4210.00, "priceMax": 4340.00, "priceYesterday": 4340.00,
             "priceFirst": 4340.00, "last": False, "id": 0, "insCode": "46348559193224090",
             "dEven": 20261021, "hEven": 123002, "pClosing": 4220.00, "iClose": False, "yClose": True,
             "pDrCotVal": 4230.00, "zTotTran": 48279.0, "qTotTran5J": 4864252101.0,
             "qTotCap": 20519267355350.00},
            {"priceChange": -110.00, "priceMin": 4290.00, "priceMax": 4510.00, "priceYesterday": 4420.00,
             "priceFirst": 4470.00, "last": False, "id": 0, "insCode": "46348559193224090",
             "dEven": 20261020, "hEven": 123001, "pClosing": 4340.00, "iClose": False, "yClose": True,
             "pDrCotVal": 4310.00, "zTotTran": 59685.0, "qTotTran5J": 5564837854.0,
             "qTotCap": 24141829641460.00},
            {"priceChange": 120.00, "priceMin": 4310.00, "priceMax": 4450.00, "priceYesterday": 4330.00,
             "priceFirst": 4450.00, "last": False, "id": 0, "insCode": "46348559193224090",
             "dEven": 20261019, "hEven": 122959, "pClosing": 4420.00, "iClose": False, "yClose": True,
             "pDrCotVal": 4450.00, "zTotTran": 53146.0, "qTotTran5J": 5199777131.0,
             "qTotCap": 22994222911090.00},
            {"priceChange": 40.00, "priceMin": 4280.00, "priceMax": 4530.00, "priceYesterday": 4410.00,
             "priceFirst": 4280.00, "last": False, "id": 0, "insCode": "46348559193224090",
             "dEven": 20261018, "hEven": 123003, "pClosing": 4330.00, "iClose": False, "yClose": True,
             "pDrCotVal": 4450.00, "zTotTran": 75929.0, "qTotTran5J": 7009626325.0,
             "qTotCap": 30364235950610.00},
            {"priceChange": -130.00, "priceMin": 4410.00, "priceMax": 4410.00, "priceYesterday": 4540.00,
             "priceFirst": 4410.00, "last": False, "id": 0, "insCode": "46348559193224090",
             "dEven": 20261017, "hEven": 122959, "pClosing": 4410.00, "iClose": False, "yClose": True,
             "pDrCotVal": 4410.00, "zTotTran": 17246.0, "qTotTran5J": 2002213699.0,
             "qTotCap": 8829762412590.00},
        ]
    }
)


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def make_provider(monkeypatch, snapshot_text: str, closing_payload: str):
    provider = TsetmcClientTypeProvider(retries=1, backoff_seconds=0.0)

    def fake_urlopen(request, timeout):
        from urllib.parse import urlsplit

        parts = urlsplit(request.full_url)
        path = parts.path
        if path.startswith("/api/Instrument/GetInstrumentSearch/"):
            assert path == f"/api/Instrument/GetInstrumentSearch/{quote('فولاد')}"
            return FakeResponse(REAL_FOOLAD_SEARCH_JSON.encode("utf-8"))
        if path == "/tsev2/data/ClientTypeAll.aspx":
            return FakeResponse(snapshot_text.encode("utf-8"))
        if path.startswith("/api/ClosingPrice/GetClosingPriceDailyList/"):
            assert parts.netloc == "cdn.tsetmc.com"
            return FakeResponse(closing_payload.encode("utf-8"))
        raise AssertionError(f"مسیر غیرمنتظره: {request.full_url}")

    monkeypatch.setattr(
        "arya.providers.shareholders.tsetmc_client_type.urlopen", fake_urlopen
    )
    return provider


# ─────────────────────────────── تست‌ها ───────────────────────────────

def test_resolve_ticker_returns_both_real_codes(monkeypatch):
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_TEXT, REAL_CLOSING_JSON)
    identity = provider.resolve_ticker("فولاد")
    assert identity.ins_code == "46348559193224090"
    assert identity.old_ins_code == "53809308236531169"
    assert identity.name == "فولاد مباركه اصفهان"


def test_snapshot_parsing_real_rows_and_structural_gate(monkeypatch):
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_TEXT, REAL_CLOSING_JSON)
    rows, rejected = provider.fetch_market_snapshot()
    assert rejected == 0
    assert len(rows) == 4
    foolad = rows["53809308236531169"]
    assert foolad.individual_buy_count == 11
    assert foolad.legal_buy_count == 3
    assert foolad.individual_buy_volume == 2511640
    assert foolad.legal_buy_volume == 1198380
    assert foolad.individual_sell_count == 27
    assert foolad.legal_sell_count == 1
    assert foolad.individual_sell_volume == 3110020
    assert foolad.legal_sell_volume == 600000
    assert foolad.total_buy_volume == foolad.total_sell_volume == 3710020
    tiny = rows["971068957336171"]
    assert tiny.total_buy_volume == tiny.total_sell_volume == 44556


def test_structural_gate_rejects_inconsistent_row(monkeypatch):
    # ردیف بعدی «سنتتیکِ فقط-تست» است: مجموع خرید (200) != مجموع فروش (600)
    broken = "9999999999,1,1,100,100,1,1,100,500"
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_TEXT + ";" + broken, REAL_CLOSING_JSON)
    rows, rejected = provider.fetch_market_snapshot()
    assert rejected == 1
    assert "9999999999" not in rows


def test_missing_flow_when_ticker_absent_from_snapshot(monkeypatch):
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_WITHOUT_FOOLAD, REAL_CLOSING_JSON)
    flow = provider.fetch_shareholder_flow("فولاد")
    assert set(flow) == set(FLOW_KEYS)
    assert flow["data_quality"] == "missing"
    assert flow["individual_avg_buy_value"] is None
    assert flow["legal_net_buy_value"] is None


def test_partial_flow_when_snapshot_date_unattributable(monkeypatch):
    """حالت واقعی ثبت‌شده در شواهد: حجم snapshot فولاد (۳٫۷۱M) با هیچ‌یک از ۵ روز بستهٔ
    واقعی (۲ تا ۷ میلیارد) تطبیق ندارد → هیچ عدد مشتق‌شده‌ای نباید تولید شود."""
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_TEXT, REAL_CLOSING_JSON)
    flow = provider.fetch_shareholder_flow("فولاد")
    assert flow["data_quality"] == "partial"
    assert flow["individual_avg_buy_value"] is None
    assert flow["individual_avg_sell_value"] is None
    assert flow["legal_buy_share"] is None
    assert flow["legal_net_buy_value"] is None
    assert flow["shareholder_count_series"] is None


def test_inspect_snapshot_reports_unattributable_with_raw_row(monkeypatch):
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_TEXT, REAL_CLOSING_JSON)
    info = provider.inspect_snapshot("فولاد")
    assert info["matched_by"] == "old_ins_code"
    assert info["row"]["total_buy_volume"] == 3710020
    assert info["attribution"]["verdict"] == "unattributable"
    assert info["attribution"]["date"] is None
    assert info["attribution"]["days_checked"] == 5
    assert 0.0 < info["attribution"]["relative_diff"] <= 1.0


def test_usable_flow_math_when_attributed_to_closing_day(monkeypatch):
    """تاریخچهٔ بسته واقعی + یک ردیف closing «سنتتیکِ فقط-تست» (حجم = حجم واقعی snapshot
    فولاد ۳٬۷۱۰٬۰۲۰ و ارزش ۷۷۹٬۱۰۴٬۲۰۰ → VWAP=۲۱۰) صرفاً برای پوشش ریاضی انتساب."""
    synthetic_closing = json.dumps(
        {
            "closingPriceDaily": [
                {"insCode": "46348559193224090", "dEven": 20261018,
                 "qTotTran5J": 3710020.0, "qTotCap": 779104200.0, "pClosing": 210.0}
            ]
        }
    )
    provider = make_provider(monkeypatch, REAL_SNAPSHOT_TEXT, synthetic_closing)
    flow = provider.fetch_shareholder_flow("فولاد")
    assert set(flow) == set(FLOW_KEYS)
    assert flow["data_quality"] == "usable"
    assert flow["legal_buy_share"] == round(1198380 / 3710020, 6)
    assert flow["individual_avg_buy_value"] == round(2511640 * 210.0 / 11, 2)
    assert flow["individual_avg_sell_value"] == round(3110020 * 210.0 / 27, 2)
    assert flow["legal_net_buy_value"] == round((1198380 - 600000) * 210.0, 2)
    assert flow["shareholder_count_series"] is None  # سری بدون تاریخ واقعی تولید نمی‌شود


def test_registry_creates_registered_driver():
    provider = ShareholderProviderRegistry.create("tsetmc_client_type", retries=1)
    assert isinstance(provider, TsetmcClientTypeProvider)
    with pytest.raises(ShareholderDataProviderError):
        ShareholderProviderRegistry.create("ناموجود")


def test_garbage_snapshot_raises_real_error(monkeypatch):
    provider = make_provider(monkeypatch, "<html>blocked</html>", REAL_CLOSING_JSON)
    with pytest.raises(ShareholderDataProviderError):
        provider.fetch_market_snapshot()
