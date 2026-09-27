import numpy as np
import pandas as pd

from app.analytics.risk import historical_var, max_drawdown, rolling_corr
from app.analytics.scenario import run_scenario
from app.econometrics.core import event_study, lag_correlations, ols


def test_max_drawdown():
    s = pd.Series([1.0, 1.2, 0.9, 1.1])
    assert abs(max_drawdown(s) - (0.9 / 1.2 - 1)) < 1e-12


def test_var_is_left_tail():
    r = pd.Series(np.linspace(-0.05, 0.05, 100))
    v = historical_var(r, 0.05)
    assert v < 0


def test_scenario_fed_hike_lifts_us_2y_more_than_30y():
    out = run_scenario(100, 0, 0, 0, 0, 0, 0)
    assert "ILLUSTRATIVE" in out["disclaimer"]
    us = out["markets"]["US"]
    assert us["d2_bp"] > us["d30_bp"]
    assert out["markets"]["IN"]["d10_bp"] > 0  # documented spillover


def test_ols_recovers_slope():
    x = pd.Series(np.arange(50, dtype=float))
    y = 2 * x + 1
    X = pd.DataFrame({"x": x})
    res = ols(y, X)
    assert res["ok"]
    slope = [t for t in res["terms"] if t["variable"] == "x"][0]
    assert abs(slope["coefficient"] - 2) < 1e-8
    assert res["r_squared"] > 0.99


def test_event_study_empty():
    s = pd.Series({pd.Timestamp("2020-01-02"): 1.0})
    res = event_study(s, [pd.Timestamp("2010-01-01")], 5)
    assert res["ok"] is False


def test_lag_corr_zero_lag_is_corr():
    a = pd.Series(np.arange(30, dtype=float), index=pd.bdate_range("2020-01-01", periods=30))
    b = a.copy()
    rows = lag_correlations(a, b, [0, 1])
    assert abs(rows[0]["correlation"] - 1) < 1e-8


def test_rolling_corr_perfect():
    idx = pd.bdate_range("2020-01-01", periods=40)
    a = pd.Series(np.arange(40, dtype=float), index=idx)
    c = rolling_corr(a, a, 10).dropna()
    assert (c.tail(5) > 0.99).all()
