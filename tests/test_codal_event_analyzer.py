"""تست تحلیل رویداد کدال و نگاشت نماد."""
from __future__ import annotations

import unittest

from arya.analysis.analyzers.codal_event_analyzer import CodalEventAnalyzer
from arya.models.codal import CodalLetter
from arya.providers.codal.symbol_map import to_codal_symbol


def _letter(title: str) -> CodalLetter:
    return CodalLetter(
        tracing_no="1",
        symbol="فولاد",
        company_name="فولاد",
        title=title,
    )


class TestSymbolMap(unittest.TestCase):
    def test_latin_to_persian(self) -> None:
        self.assertEqual(to_codal_symbol("FOOLAD"), "فولاد")
        self.assertEqual(to_codal_symbol("فولاد"), "فولاد")


class TestCodalEventAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = CodalEventAnalyzer()

    def test_empty(self) -> None:
        s = self.analyzer.analyze([])
        self.assertEqual(s.score, 0.0)
        self.assertEqual(s.confidence, 0.0)

    def test_capital_increase(self) -> None:
        s = self.analyzer.analyze([_letter("تصمیمات افزایش سرمایه شرکت")])
        self.assertGreater(s.score, 0)
        self.assertGreater(s.confidence, 0)
        self.assertTrue(any("افزایش" in r for r in s.details["reasons"]))

    def test_halt(self) -> None:
        s = self.analyzer.analyze([_letter("توقف نماد به دلیل")])
        self.assertLess(s.score, 0)


if __name__ == "__main__":
    unittest.main()
