"""فاز ۰ — گیت شواهد (Evidence Gate) برای دادهٔ واقعی سهامداران TSETMC.

پروب مستقیم endpointهای واقعی و ثبت خام شواهد در docs/sources/evidence/2026-10-24/.
هیچ پاسخی شبیه‌سازی نمی‌شود؛ آنچه دریافت نشود، «ناموفق» ثبت می‌شود.
"""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

EVIDENCE_DIR = "/home/z/my-project/repo_arya/docs/sources/evidence/2026-10-24"
UA = "ARYA-AI-Trader/0.1 (+https://github.com/ziya1346/ARYA_AI_TRADER)"
TIMEOUT = 25.0
MAX_SAVE_BYTES = 400_000  # فایل‌های شواهد را محدود نگه می‌داریم

os.makedirs(EVIDENCE_DIR, exist_ok=True)

socket.setdefaulttimeout(TIMEOUT)


def fetch(url: str, headers: dict | None = None) -> dict:
    """یک درخواست واقعی؛ خروجی: متادیتا + بدنهٔ خام (bytes) یا خطا."""
    request = Request(url, headers={"User-Agent": UA, **(headers or {})})
    started = datetime.now(timezone.utc)
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            body = response.read()
            return {
                "url": url,
                "status": response.status,
                "headers": {k: v for k, v in response.headers.items()
                            if k.lower() in {"content-type", "server", "date", "content-length"}},
                "body": body,
                "elapsed_ms": int((datetime.now(timezone.utc) - started).total_seconds() * 1000),
            }
    except HTTPError as exc:
        return {"url": url, "status": exc.code, "error": f"HTTPError: {exc.reason}",
                "body": b"", "elapsed_ms": int((datetime.now(timezone.utc) - started).total_seconds() * 1000)}
    except Exception as exc:  # noqa: BLE001 — پروب است؛ هر خطایی باید ثبت شود
        return {"url": url, "status": None, "error": f"{type(exc).__name__}: {exc}",
                "body": b"", "elapsed_ms": int((datetime.now(timezone.utc) - started).total_seconds() * 1000)}


def save_evidence(name: str, result: dict) -> None:
    meta = {k: v for k, v in result.items() if k != "body"}
    meta["captured_at_utc"] = datetime.now(timezone.utc).isoformat()
    meta["agent"] = "phase0_evidence.py (ARYA CR-20261024-002 فاز ۰)"
    body = result.get("body") or b""
    meta["body_bytes"] = len(body)
    ok = result.get("status") == 200 and len(body) > 0
    meta["verdict"] = "VERIFIED" if ok else "FAILED"
    with open(os.path.join(EVIDENCE_DIR, f"{name}.meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    if len(body) > MAX_SAVE_BYTES:
        body = body[:MAX_SAVE_BYTES]
    with open(os.path.join(EVIDENCE_DIR, f"{name}.raw{'.' + ext(name) if ext(name) else ''}"), "wb") as fh:
        fh.write(body)
    print(f"[{meta['verdict']:8}] {name}: status={result.get('status')} bytes={len(body)} "
          f"{result.get('error') or ''}")


def ext(name: str) -> str:
    if "wsdl" in name or "asmx" in name:
        return "xml"
    if "docs" in name and "api" in name:
        return "html"
    return "json"


def main() -> None:
    # ── مرحلهٔ ۱: نگاشت نماد واقعی → insCode (منبع: جست‌وجوی رسمی cdn.tsetmc.com) ──
    probes: list[tuple[str, str]] = [
        ("01_cdn_search Foolad".replace(" ", "_"),
         "https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/" + quote("فولاد")),
        ("02_api_tsetmc_docs", "https://api.tsetmc.com/docs"),
        ("03_service_wsdl", "https://service.tsetmc.com/webservice/TsePublicV2.asmx?WSDL"),
        ("04_service_op_sharechange",
         "https://service.tsetmc.com/webservice/TsePublicV2.asmx?op=ShareChange"),
        ("05_cdn_marketwatch_compact",
         "https://cdn.tsetmc.com/api/ClosingPrice/GetMarketWatch?market=0&paperTypes[0]=1"
         "&paperTypes[1]=2&paperTypes[2]=3&paperTypes[3]=4&paperTypes[4]=5&paperTypes[5]=6"
         "&paperTypes[6]=7&paperTypes[7]=8&paperTypes[8]=9&withBestLimits=false&hEven=0&RefID=0"),
    ]
    results = {}
    for name, url in probes:
        r = fetch(url)
        results[name] = r
        save_evidence(name, r)

    # ── مرحلهٔ ۲: با insCode واقعیِ به‌دست‌آمده، ClientType و Shareholder را پروب کن ──
    ins_code = None
    body = results.get("01_cdn_search_Foolad", {}).get("body") or b""
    if body:
        try:
            rows = json.loads(body.decode("utf-8-sig")).get("instrumentSearch", [])
            for row in rows:
                if str(row.get("lVal18AFC") or "").strip() == "فولاد":
                    ins_code = str(row["insCode"])
                    break
            if ins_code is None and rows:
                ins_code = str(rows[0].get("insCode"))
        except Exception as exc:  # noqa: BLE001
            print(f"parse search failed: {exc}")

    print(f"resolved insCode = {ins_code}")
    if ins_code:
        # دو روز معاملهٔ اخیر (چهارشنبه ۱۴۰۵/۰۷/۳۰ = 2026-10-22 و سه‌شنبه 2026-10-21)
        for ymd in ("20261022", "20261021"):
            save_evidence(
                f"06_cdn_clienttype_{ins_code}_{ymd}",
                fetch(f"https://cdn.tsetmc.com/api/ClientType/GetClientType/{ins_code}/{ymd}"),
            )
        save_evidence(
            f"07_cdn_shareholder_{ins_code}",
            fetch(f"https://cdn.tsetmc.com/api/Shareholder/{ins_code}"),
        )
        save_evidence(
            f"08_cdn_shareholder_history_{ins_code}",
            fetch(f"https://cdn.tsetmc.com/api/Shareholder/GetShareholderHistory/{ins_code}"),
        )
        save_evidence(
            f"09_old_clienttype_all_{ins_code}",
            fetch(f"https://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx?t={ins_code}"),
        )
    else:
        print("!! insCode resolve نشد — پروب‌های وابسته رد شدند (شواهد FAIL ثبت می‌شود)")
        for name in ("06_cdn_clienttype", "07_cdn_shareholder", "08_cdn_shareholder_history",
                     "09_old_clienttype_all"):
            save_evidence(name + "_SKIPPED", {"url": "(skipped: no insCode)", "status": None,
                                              "error": "insCode not resolved", "body": b""})

    # ── خلاصهٔ نهایی ──
    print("\n=== SUMMARY ===")
    for fn in sorted(os.listdir(EVIDENCE_DIR)):
        if fn.endswith(".meta.json"):
            with open(os.path.join(EVIDENCE_DIR, fn), encoding="utf-8") as fh:
                m = json.load(fh)
            print(f"{m['verdict']:8} {m['url'][:110]}")


if __name__ == "__main__":
    main()
