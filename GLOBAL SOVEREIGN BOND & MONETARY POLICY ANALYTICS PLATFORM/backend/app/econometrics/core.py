from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def ols(y: pd.Series, X: pd.DataFrame) -> dict:
    aligned = pd.concat([y, X], axis=1).dropna()
    if aligned.empty or len(aligned) < 12:
        return {"ok": False, "error": "Insufficient overlapping observations (need ≥ 12)."}
    yv = aligned.iloc[:, 0]
    xv = sm.add_constant(aligned.iloc[:, 1:], has_constant="add")
    model = sm.OLS(yv, xv).fit()
    terms = []
    for name, coef, se, t, p in zip(
        model.params.index, model.params, model.bse, model.tvalues, model.pvalues
    ):
        terms.append(
            {
                "variable": str(name),
                "coefficient": float(coef),
                "std_error": float(se),
                "t_stat": float(t),
                "p_value": float(p),
            }
        )
    warnings = [
        "OLS coefficients describe association within this sample, not causation.",
        "Sovereign yields are persistent; residuals are often autocorrelated, so t-stats can be overstated.",
        "Omitted variables (global risk, FX, oil, fiscal) may bias coefficients.",
        "Policy rates and yields are jointly determined — endogeneity is likely.",
        "Structural breaks (COVID, the 2022 inflation shock) can invalidate a single-regime fit.",
    ]
    return {
        "ok": True,
        "n": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "terms": terms,
        "warnings": warnings,
    }


def lag_correlations(a: pd.Series, b: pd.Series, lags: list[int]) -> list[dict]:
    """Corr(a_t, b_{t-lag}). Positive lag: b leads a."""
    aligned = pd.concat([a, b], axis=1).dropna()
    aligned.columns = ["a", "b"]
    out = []
    for lag in lags:
        if lag == 0:
            c = aligned["a"].corr(aligned["b"])
        else:
            c = aligned["a"].corr(aligned["b"].shift(lag))
        out.append({"lag": lag, "correlation": None if pd.isna(c) else float(c)})
    return out


def corr_matrix(df: pd.DataFrame) -> dict:
    c = df.corr()
    return {
        "labels": list(c.columns),
        "matrix": [[None if pd.isna(v) else float(v) for v in row] for row in c.values],
        "n": int(df.dropna().shape[0]),
    }


def event_study(series: pd.Series, event_dates: list, window: int = 10) -> dict:
    """Average change in the series (in bp if series is in percent) around events."""
    s = series.dropna().sort_index()
    paths = []
    used = []
    for d in event_dates:
        ts = pd.Timestamp(d)
        if ts not in s.index:
            loc = s.index.searchsorted(ts)
            if loc >= len(s.index):
                continue
            ts = s.index[loc]
        loc = s.index.get_loc(ts)
        if isinstance(loc, slice):
            loc = loc.start
        if loc - window < 0 or loc + window >= len(s):
            continue
        window_vals = s.iloc[loc - window : loc + window + 1]
        base = window_vals.iloc[window]
        path = (window_vals - base) * 100.0  # percentage points → bp
        paths.append(path.values)
        used.append(str(pd.Timestamp(ts).date()))
    if not paths:
        return {"ok": False, "error": "No policy events match the selected window.", "n": 0}
    arr = np.vstack(paths)
    days = list(range(-window, window + 1))
    points = []
    for i, day in enumerate(days):
        col = arr[:, i]
        points.append(
            {
                "day": day,
                "mean_bp": float(np.mean(col)),
                "median_bp": float(np.median(col)),
                "p25_bp": float(np.percentile(col, 25)),
                "p75_bp": float(np.percentile(col, 75)),
                "max_bp": float(np.max(col)),
                "min_bp": float(np.min(col)),
                "n": int(arr.shape[0]),
            }
        )
    terminal = arr[:, -1]
    pre_vol = arr[:, : window].std(axis=1).mean() if window else 0
    post_vol = arr[:, window + 1 :].std(axis=1).mean() if window else 0
    return {
        "ok": True,
        "n": int(arr.shape[0]),
        "events_used": used,
        "points": points,
        "avg_terminal_bp": float(np.mean(terminal)),
        "median_terminal_bp": float(np.median(terminal)),
        "max_increase_bp": float(np.max(arr)),
        "max_decrease_bp": float(np.min(arr)),
        "vol_pre_bp": float(pre_vol),
        "vol_post_bp": float(post_vol),
        "methodology": (
            "Each event path is demeaned at t=0 (the event day). "
            "The chart shows the average cumulative yield change in basis points "
            "relative to the event-day level. This is an event study, not a causal estimate."
        ),
    }
