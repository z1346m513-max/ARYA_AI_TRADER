from importlib import import_module

from arya.app.bootstrap import MarketDataSafetyError


cli = import_module("arya.cli.main")


class BlockedApp:
    def analyze_symbol(self, *_args, **_kwargs):
        raise MarketDataSafetyError("driver='mock' داده مصنوعی تولید می‌کند")


def test_cli_stops_and_returns_nonzero_for_synthetic_provider(monkeypatch, capsys):
    monkeypatch.setattr(cli, "AryaApp", BlockedApp)

    result = cli.main(["analyze", "--ticker", "BTCUSDT", "--market", "crypto"])

    captured = capsys.readouterr()
    assert result == 2
    assert "اجرا متوقف شد" in captured.err
    assert "داده مصنوعی" in captured.err
