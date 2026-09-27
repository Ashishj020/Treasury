from __future__ import annotations

import numpy as np
import pandas as pd


def resample_series(s: pd.Series, frequency: str) -> pd.Series:
    rule = {"daily": "B", "weekly": "W-FRI", "monthly": "ME"}.get(frequency, "B")
    return s.resample(rule).last().dropna()


def to_bp(delta_pp: float | np.ndarray) -> float | np.ndarray:
    return np.asarray(delta_pp) * 100.0


def yield_change(s: pd.Series, periods: int) -> float | None:
    s = s.dropna()
    if len(s) <= periods:
        return None
    return float(s.iloc[-1] - s.iloc[-1 - periods])


def rolling_vol(returns: pd.Series, window: int, annualize: int = 252) -> pd.Series:
    return returns.rolling(window).std() * np.sqrt(annualize)


def max_drawdown(cum: pd.Series) -> float:
    peak = cum.cummax()
    dd = cum / peak - 1.0
    return float(dd.min()) if len(dd) else 0.0


def drawdown_series(cum: pd.Series) -> pd.Series:
    peak = cum.cummax()
    return cum / peak - 1.0


def historical_var(returns: pd.Series, alpha: float = 0.05) -> float | None:
    r = returns.dropna()
    if len(r) < 30:
        return None
    return float(np.quantile(r, alpha))


def sharpe(returns: pd.Series, rf_daily: float = 0.0, annualize: int = 252) -> float | None:
    r = returns.dropna()
    if len(r) < 30 or r.std() == 0:
        return None
    excess = r - rf_daily
    return float(np.sqrt(annualize) * excess.mean() / excess.std())


def rolling_corr(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    aligned = pd.concat([a, b], axis=1).dropna()
    if aligned.empty:
        return pd.Series(dtype=float)
    return aligned.iloc[:, 0].rolling(window).corr(aligned.iloc[:, 1])


def rolling_beta(y: pd.Series, x: pd.Series, window: int) -> pd.Series:
    aligned = pd.concat([y, x], axis=1).dropna()
    aligned.columns = ["y", "x"]
    cov = aligned["y"].rolling(window).cov(aligned["x"])
    var = aligned["x"].rolling(window).var()
    return cov / var.replace(0, np.nan)
