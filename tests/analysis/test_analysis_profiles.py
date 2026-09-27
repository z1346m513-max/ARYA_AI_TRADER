from arya.config.settings import Settings


def test_analysis_profile_applies_indicator_and_decision_overrides():
    settings = Settings.load()
    tuned = settings.for_analysis(profile_name="momentum")

    assert tuned.analysis["runtime"]["history_limit"] == 250
    assert tuned.indicators["momentum"]["rsi"]["params"]["period"] == 9
    assert tuned.indicators["momentum"]["rsi"]["params"]["overbought"] == 72
    assert tuned.indicators["momentum"]["macd"]["params"]["fast"] == 8
    assert tuned.analysis["runtime"]["decision"]["buy_threshold"] == 0.20


def test_runtime_overrides_are_isolated_from_base_settings():
    settings = Settings.load()
    tuned = settings.for_analysis(
        indicator_overrides={
            "trend": {"sma": {"params": {"period": 100}, "enabled": False}}
        },
        decision_overrides={"buy_threshold": 0.50, "sell_threshold": -0.50},
        history_limit=400,
    )

    assert tuned.indicators["trend"]["sma"]["params"]["period"] == 100
    assert tuned.indicators["trend"]["sma"]["enabled"] is False
    assert tuned.analysis["runtime"]["history_limit"] == 400
    assert tuned.analysis["runtime"]["decision"]["buy_threshold"] == 0.50
    assert settings.indicators["trend"]["sma"]["params"]["period"] == 20
    assert settings.indicators["trend"]["sma"]["enabled"] is True
