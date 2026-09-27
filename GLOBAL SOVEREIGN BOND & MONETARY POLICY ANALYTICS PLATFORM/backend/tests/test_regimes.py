from app.analytics.bond import classify_policy_cycle, classify_policy_regime


def test_regime_thresholds():
    assert classify_policy_regime(40, False, False) == "HAWKISH"
    assert classify_policy_regime(-40, False, False) == "DOVISH"
    assert classify_policy_regime(0, False, False) == "NEUTRAL"
    assert classify_policy_regime(0, True, False) == "DOVISH"
    assert classify_policy_regime(0, False, True) == "HAWKISH"


def test_cycle():
    assert classify_policy_cycle(80, 5.0, 5.5) == "HIKING"
    assert classify_policy_cycle(-80, 4.0, 5.5) == "CUTTING"
    assert classify_policy_cycle(0, 5.4, 5.5) == "PEAK"
