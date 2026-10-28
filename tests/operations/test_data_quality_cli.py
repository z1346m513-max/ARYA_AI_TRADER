from arya.cli import main as cli_main
from arya.data_quality import OHLCVQualityError, OHLCVQualityReport, QualityIssue


def test_cli_reports_quality_rejection_without_traceback(monkeypatch, capsys):
    class FakeApp:
        def __init__(self):
            pass

        def analyze_symbol(self, *args, **kwargs):
            report = OHLCVQualityReport(
                is_valid=False,
                row_count=1,
                first_timestamp="2026-01-01T00:00:00+00:00",
                last_timestamp="2026-01-01T00:00:00+00:00",
                issues=(QualityIssue("duplicate_timestamp", "زمان کندل تکراری است", 0),),
            )
            raise OHLCVQualityError(report)

    monkeypatch.setattr("arya.cli.main.AryaApp", FakeApp)
    assert cli_main.main(["analyze", "--ticker", "TEST"]) == 2
    output = " ".join(capsys.readouterr().out.split())
    assert "کنترل کیفیت داده رد شد" in output
    assert "زمان کندل تکراری است" in output
