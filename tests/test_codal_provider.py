"""تست واحد CodalProvider با پاسخ شبیه‌سازی‌شده (بدون شبکه)."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from arya.providers.codal.codal_provider import CodalProvider, CodalProviderError


SAMPLE = {
    "Total": 2,
    "Page": 1,
    "Letters": [
        {
            "TracingNo": "123",
            "Symbol": "فولاد",
            "CompanyName": "فولاد مبارکه اصفهان",
            "Title": "اطلاعات و صورت‌های مالی میان‌دوره‌ای",
            "SentDateTime": "1403/10/01 12:00:00",
            "PublishDateTime": "1403/10/01 12:05:00",
            "Url": "/ReportList.aspx?x=1",
            "HasHtml": True,
        },
        {
            "TracingNo": "124",
            "Symbol": "فولاد",
            "CompanyName": "فولاد مبارکه اصفهان",
            "Title": "تصمیمات مجمع",
            "SentDateTime": "1403/09/20 10:00:00",
            "PublishDateTime": "1403/09/20 10:10:00",
        },
    ],
}


class TestCodalProvider(unittest.TestCase):
    def test_map_and_search(self) -> None:
        provider = CodalProvider(min_interval_seconds=0)

        def fake_get(path, params=None):
            self.assertEqual(path, "/v2/q")
            self.assertEqual(params["Symbol"], "فولاد")
            return SAMPLE

        with patch.object(provider, "_get_json", side_effect=fake_get):
            letters, total = provider.search_letters("فولاد", page=1)
        self.assertEqual(total, 2)
        self.assertEqual(len(letters), 2)
        self.assertEqual(letters[0].symbol, "فولاد")
        self.assertIn("صورت", letters[0].title)

    def test_empty_symbol(self) -> None:
        provider = CodalProvider(min_interval_seconds=0)
        with self.assertRaises(ValueError):
            provider.search_letters("  ")


if __name__ == "__main__":
    unittest.main()
