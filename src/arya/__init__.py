"""ARYA AI Trader — پلتفرم تحلیل بورس ایران."""

from __future__ import annotations

import sys

__version__ = "0.2.0-tse-codal"

# پشتیبانی رسمی: CPython 3.10 … 3.15
_MIN = (3, 10)
_MAX_EXCLUSIVE = (3, 16)


def _check_python() -> None:
    v = sys.version_info[:2]
    if v < _MIN or v >= _MAX_EXCLUSIVE:
        raise RuntimeError(
            f"ARYA به Python >=3.10 و <3.16 نیاز دارد؛ نسخه فعلی: "
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
            f"روی 3.15 از venv تازه و pip به‌روز استفاده کنید: python -m pip install -U pip setuptools wheel"
        )


_check_python()
