from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.bond import (
    bond_price,
    classify_curve,
    classify_policy_cycle,
    classify_policy_regime,
    convexity,
    current_yield,
    duration_price_change,
    macaulay_duration,
    modified_duration,
)
from app.analytics.risk import (
    drawdown_series,
    historical_var,
    max_drawdown,
    rolling_beta,
    rolling_corr,
    rolling_vol,
    sharpe,
)
from app.analytics.scenario import run_scenario
from app.config import get_settings
from app.database import get_db
from app.econometrics.core import corr_matrix, event_study, lag_correlations, ols
from app.models.tables import (
    CentralBank,
    Country,
    DataSource,
    MacroIndicator,
    MarketEvent,
    PolicyEvent,
    PolicyRate,
    SovereignYield,
)
from app.schemas.market import BondLabRequest, ScenarioRequest
from app.services import query as Q

router = APIRouter(prefix="/api")

TENOR_YEARS = {"3M": 0.25, "6M": 0.5, "1Y": 1, "2Y": 2, "5Y": 5, "10Y": 10, "20Y": 20, "30Y": 30}
FREQ_RULE = {"daily": None, "weekly": "W-FRI", "monthly": "ME"}


def _resample(s: pd.Series, frequency: str) -> pd.Series:
    rule = FREQ_RULE.get(frequency, None)
    if not rule:
        return s
    return s.resample(rule).last().dropna()


def _last_date(db: Session) -> date:
    row = db.query(SovereignYield.date).order_by(SovereignYield.date.desc()).first()
    return row[0] if row else date(2026, 9, 16)


@router.get("/health")
def health():
    s = get_settings()
    return {"ok": True, "demo_mode": s.demo_mode, "name": s.app_name}


@router.get("/markets")
def markets(db: Session = Depends(get_db)):
    rows = db.query(Country, CentralBank).join(CentralBank, CentralBank.country_id == Country.id).all()
    return [
        {
            "code": c.code,
            "name": c.name,
            "region": c.region,
            "currency": c.currency,
            "central_bank": cb.name,
            "central_bank_code": cb.code,
            "policy_rate_name": cb.policy_rate_name,
            "benchmark_label": c.benchmark_label,
        }
        for c, cb in rows
    ]


@router.get("/status")
def status(db: Session = Depends(get_db)):
    last = _last_date(db)
    items = []
    for c in db.query(Country).all():
        n = db.query(SovereignYield).filter(SovereignYield.country_id == c.id).count()
        items.append(
            {
                "market": c.code,
                "source": "SIMULATED — Treasury/RBI/BoE/ECB-inspired",
                "status": "Available",
                "last_updated": last,
                "observations": n,
                "frequency": "daily",
                "missing": 0,
                "demo": True,
            }
        )
    return {
        "demo_mode": True,
        "label": "DEMO MODE ACTIVE",
        "disclaimer": "SIMULATED DATA — FOR ANALYTICAL DEMONSTRATION",
        "last_updated": last,
        "items": items,
    }


@router.get("/overview")
def overview(
    range: str = Query("5Y"),
    frequency: str = Query("daily"),
    db: Session = Depends(get_db),
):
    end = _last_date(db)
    start = Q.window_start(end, range)
    kpis = []
    for mkt, label in [("US", "US 10Y"), ("IN", "India 10Y"), ("UK", "UK 10Y"), ("EZ", "Germany 10Y")]:
        s = _resample(Q.yield_frame(db, mkt, "10Y", start, end), frequency)
        if s.empty:
            continue
        kpis.append(
            {
                "market": mkt,
                "label": label,
                "current": float(s.iloc[-1]),
                "change_1d_bp": float((s.iloc[-1] - s.iloc[-2]) * 100) if len(s) > 1 else None,
                "change_1m_bp": float((s.iloc[-1] - s.iloc[-22]) * 100) if len(s) > 22 else None,
                "change_1y_bp": float((s.iloc[-1] - s.iloc[-252]) * 100) if len(s) > 252 else None,
                "sparkline": [round(float(x), 3) for x in s.tail(60).tolist()],
            }
        )
    policy_cards = []
    for mkt in ("US", "IN", "UK", "EZ"):
        p = Q.policy_frame(db, mkt, start, end)
        if p.empty:
            continue
        d90 = float((p.iloc[-1] - p.iloc[-63]) * 100) if len(p) > 63 else 0.0
        qe = False
        qt = False
        # last QE/QT from events nearby
        policy_cards.append(
            {
                "market": mkt,
                "current": float(p.iloc[-1]),
                "change_90d_bp": d90,
                "sparkline": [round(float(x), 3) for x in p.tail(60).tolist()],
            }
        )

    heat = []
    for mkt in ("US", "IN", "UK", "EZ"):
        p = Q.policy_frame(db, mkt)
        y2 = Q.yield_frame(db, mkt, "2Y")
        y10 = Q.yield_frame(db, mkt, "10Y")
        d90 = float((p.iloc[-1] - p.iloc[-63]) * 100) if len(p) > 63 else 0
        d180 = float((p.iloc[-1] - p.iloc[-126]) * 100) if len(p) > 126 else 0
        peak = float(p.max())
        hiking = d90 >= 12
        cutting = d90 <= -12
        holding = not hiking and not cutting
        slope = float(y10.iloc[-1] - y2.iloc[-1]) if len(y10) and len(y2) else None
        last_ev = (
            db.query(PolicyEvent)
            .join(CentralBank)
            .filter(CentralBank.country_id == Q.country_by_code(db, mkt).id)
            .order_by(PolicyEvent.date.desc())
            .first()
        )
        qe = bool(last_ev and last_ev.event_type == "QE")
        qt = bool(last_ev and last_ev.event_type == "QT")
        # look at recent 400d for QE/QT flags via event types
        recent = (
            db.query(PolicyEvent)
            .join(CentralBank)
            .filter(CentralBank.country_id == Q.country_by_code(db, mkt).id, PolicyEvent.date >= end - timedelta(days=900))
            .all()
        )
        qe = any(e.event_type == "QE" for e in recent) and d90 <= 0
        qt = any(e.event_type == "QT" for e in recent) and d90 >= 0
        heat.append(
            {
                "market": mkt,
                "regime": classify_policy_regime(d90, qe, qt),
                "cycle": classify_policy_cycle(d180, float(p.iloc[-1]), peak),
                "hiking": hiking,
                "cutting": cutting,
                "holding": holding,
                "qe": qe,
                "qt": qt,
                "policy_rate": float(p.iloc[-1]),
                "slope_2s10s": slope,
            }
        )

    # mood from average 2s10s and vix-like vol
    slopes = [h["slope_2s10s"] for h in heat if h["slope_2s10s"] is not None]
    avg_slope = float(np.mean(slopes)) if slopes else 0
    if any(h["hiking"] for h in heat) and avg_slope < 0:
        mood = {"code": "POLICY UNCERTAINTY", "tone": "violet"}
    elif avg_slope < -0.2:
        mood = {"code": "RISK-OFF", "tone": "red"}
    elif all(h["holding"] or h["cutting"] for h in heat):
        mood = {"code": "WAIT & SEE", "tone": "amber"}
    else:
        mood = {"code": "RISK-ON", "tone": "green"}

    insights = _overview_insights(kpis, heat)
    return {"asof": end, "kpis": kpis, "policy": policy_cards, "heatmap": heat, "mood": mood, "insights": insights}


def _overview_insights(kpis, heat) -> list[dict]:
    out = []
    if len(kpis) >= 2:
        ranked = sorted(kpis, key=lambda k: abs(k.get("change_1y_bp") or 0), reverse=True)
        a, b = ranked[0], ranked[-1]
        if a.get("change_1y_bp") is not None:
            out.append(
                {
                    "title": "WHAT CHANGED?",
                    "body": (
                        f"During the selected window the largest 1Y 10Y move in this sample is "
                        f"{a['label']} ({a['change_1y_bp']:+.1f} bp) versus {b['label']} "
                        f"({(b.get('change_1y_bp') or 0):+.1f} bp). This is an observation, not a forecast."
                    ),
                    "a": a["change_1y_bp"],
                    "b": b.get("change_1y_bp"),
                }
            )
    hikers = [h["market"] for h in heat if h["hiking"]]
    cutters = [h["market"] for h in heat if h["cutting"]]
    out.append(
        {
            "title": "POLICY REGIME",
            "body": (
                f"Transparent 90-day rule: hiking {hikers or '—'}; cutting {cutters or '—'}. "
                f"Classification uses the change in the policy rate, not a model of the reaction function."
            ),
        }
    )
    return out


@router.get("/series")
def series(
    market: str,
    maturity: str = "10Y",
    range: str = "5Y",
    frequency: str = "daily",
    db: Session = Depends(get_db),
):
    end = _last_date(db)
    start = Q.window_start(end, range)
    y = _resample(Q.yield_frame(db, market, maturity, start, end), frequency)
    p = _resample(Q.policy_frame(db, market, start, end), frequency)
    y2 = _resample(Q.yield_frame(db, market, "2Y", start, end), frequency)
    y10 = _resample(Q.yield_frame(db, market, "10Y", start, end), frequency)
    y30 = _resample(Q.yield_frame(db, market, "30Y", start, end), frequency)
    aligned = pd.concat([p, y, y2, y10, y30], axis=1)
    aligned.columns = ["policy", "y", "y2", "y10", "y30"]
    aligned = aligned.dropna(how="all")
    events = db.query(MarketEvent).filter(MarketEvent.date >= start, MarketEvent.date <= end).all()
    return {
        "market": Q.code(market),
        "maturity": maturity,
        "disclaimer": "SIMULATED DATA — FOR ANALYTICAL DEMONSTRATION",
        "points": [
            {
                "date": idx.date().isoformat(),
                "policy": None if pd.isna(r.policy) else float(r.policy),
                "yield": None if pd.isna(r.y) else float(r.y),
                "y2": None if pd.isna(r.y2) else float(r.y2),
                "y10": None if pd.isna(r.y10) else float(r.y10),
                "y30": None if pd.isna(r.y30) else float(r.y30),
                "spread_2s10s": None if pd.isna(r.y10) or pd.isna(r.y2) else float(r.y10 - r.y2),
            }
            for idx, r in aligned.iterrows()
        ],
        "events": [
            {
                "date": e.date.isoformat(),
                "code": e.code,
                "title": e.title,
                "category": e.category,
                "description": e.description,
                "markets": e.markets,
            }
            for e in events
        ],
    }


@router.get("/yield-curve")
def yield_curve(
    market: str = "US",
    asof: date | None = None,
    compare: str | None = None,
    db: Session = Depends(get_db),
):
    end = asof or _last_date(db)
    snap = Q.curve_on(db, market, end)
    d0 = snap.pop("_date")
    pts = [{"maturity": k, "tenor_years": TENOR_YEARS[k], "yield_pct": snap[k]} for k in TENOR_YEARS if k in snap]
    s2 = snap.get("2Y")
    s10 = snap.get("10Y")
    s5 = snap.get("5Y")
    s30 = snap.get("30Y")
    spread_2s10s = (s10 - s2) if s2 is not None and s10 is not None else 0
    shape, personality = classify_curve(spread_2s10s)
    overlays = []
    offsets = {"1M": 30, "3M": 91, "1Y": 365, "5Y": 365 * 5}
    if compare:
        keys = [c.strip() for c in compare.split(",") if c.strip()]
    else:
        keys = ["1M", "3M", "1Y"]
    for key in keys:
        if key in offsets:
            prev = Q.curve_on(db, market, d0 - timedelta(days=offsets[key]))
            pd0 = prev.pop("_date")
            overlays.append(
                {
                    "label": key,
                    "asof": pd0.isoformat(),
                    "points": [
                        {"maturity": k, "tenor_years": TENOR_YEARS[k], "yield_pct": prev[k]}
                        for k in TENOR_YEARS
                        if k in prev
                    ],
                }
            )
    return {
        "market": Q.code(market),
        "asof": d0.isoformat(),
        "points": pts,
        "shape": shape,
        "personality": personality,
        "spread_2s10s": spread_2s10s,
        "spread_5s30s": (s30 - s5) if s30 is not None and s5 is not None else None,
        "spread_10s30s": (s30 - s10) if s30 is not None and s10 is not None else None,
        "overlays": overlays,
        "disclaimer": "SIMULATED DATA — FOR ANALYTICAL DEMONSTRATION",
    }


@router.get("/policy-rates")
def policy_rates(range: str = "MAX", db: Session = Depends(get_db)):
    end = _last_date(db)
    start = Q.window_start(end, range)
    out = {}
    for mkt in ("US", "IN", "UK", "EZ"):
        s = Q.policy_frame(db, mkt, start, end)
        out[mkt] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in s.items()]
    return out


@router.get("/events")
def events(cb: str | None = None, db: Session = Depends(get_db)):
    rows = Q.policy_events(db, cb)
    out = []
    for ev, bank in rows:
        c = db.query(Country).filter(Country.id == bank.country_id).one()
        y = Q.curve_on(db, c.code, ev.date)
        before = Q.curve_on(db, c.code, ev.date - timedelta(days=5))
        after = Q.curve_on(db, c.code, ev.date + timedelta(days=5))
        def grab(snap, k):
            return snap.get(k)
        out.append(
            {
                "id": ev.id,
                "date": ev.date.isoformat(),
                "cb": bank.code,
                "market": c.code,
                "event_type": ev.event_type,
                "policy_rate": ev.policy_rate,
                "change_bp": ev.change_bp,
                "decision": ev.decision,
                "rationale": ev.rationale,
                "before": {"2Y": grab(before, "2Y"), "10Y": grab(before, "10Y"), "30Y": grab(before, "30Y")},
                "event": {"2Y": grab(y, "2Y"), "10Y": grab(y, "10Y"), "30Y": grab(y, "30Y")},
                "after": {"2Y": grab(after, "2Y"), "10Y": grab(after, "10Y"), "30Y": grab(after, "30Y")},
            }
        )
    market = [
        {
            "date": e.date.isoformat(),
            "code": e.code,
            "title": e.title,
            "category": e.category,
            "description": e.description,
            "markets": e.markets,
        }
        for e in db.query(MarketEvent).order_by(MarketEvent.date).all()
    ]
    return {"policy": out, "market": market}


@router.get("/event-study")
def event_study_api(
    cb: str = "FED",
    event_type: str = "HIKE",
    window: int = 10,
    market: str | None = None,
    maturity: str = "10Y",
    db: Session = Depends(get_db),
):
    window = int(window)
    if window not in (1, 5, 10, 30):
        raise HTTPException(400, "window must be 1, 5, 10 or 30")
    rows = Q.policy_events(db, cb)
    dates = [ev.date for ev, _ in rows if ev.event_type.upper() == event_type.upper()]
    if not dates:
        # HOLD is stored as HOLD; QE/QT as those codes
        dates = [ev.date for ev, _ in rows if event_type.upper() in ev.event_type.upper() or event_type.upper() in ev.decision.upper()]
    mkt = market or {"FED": "US", "RBI": "IN", "BOE": "UK", "ECB": "EZ"}.get(cb.upper(), "US")
    s = Q.yield_frame(db, mkt, maturity)
    result = event_study(s, dates, window)
    result["cb"] = cb.upper()
    result["event_type"] = event_type.upper()
    result["market"] = Q.code(mkt)
    result["maturity"] = maturity
    result["disclaimer"] = "Observed average path in DEMO data. Not a causal estimate."
    return result


@router.get("/returns")
def returns_api(maturity: str = "10Y", range: str = "MAX", db: Session = Depends(get_db)):
    end = _last_date(db)
    start = Q.window_start(end, range)
    series = {}
    stats = {}
    for mkt in ("US", "IN", "UK", "EZ"):
        df = Q.returns_components(db, mkt, maturity)
        df = df[df.index >= pd.Timestamp(start)]
        if df.empty:
            continue
        cum = (1 + df["total_return"]).cumprod()
        dd = drawdown_series(cum)
        series[mkt] = [
            {
                "date": i.date().isoformat(),
                "total_return": float(r.total_return),
                "price_return": float(r.price_return),
                "coupon_return": float(r.coupon_return),
                "cumulative": float(cum.loc[i]),
                "drawdown": float(dd.loc[i]),
            }
            for i, r in df.iterrows()
        ]
        roll12 = (1 + df["total_return"]).rolling(252).apply(lambda x: np.prod(x) - 1, raw=True)
        stats[mkt] = {
            "ann_return": float(df["total_return"].mean() * 252),
            "ann_vol": float(df["total_return"].std() * np.sqrt(252)),
            "max_drawdown": max_drawdown(cum),
            "sharpe": sharpe(df["total_return"]),
            "price_share": float(df["price_return"].sum() / df["total_return"].sum()) if df["total_return"].sum() else None,
            "last_12m": None if roll12.dropna().empty else float(roll12.dropna().iloc[-1]),
        }
    return {
        "maturity": maturity,
        "benchmarks": {
            "US": "Simulated constant-maturity UST 10Y total return",
            "IN": "Simulated constant-maturity G-Sec 10Y total return",
            "UK": "Simulated constant-maturity gilt 10Y total return",
            "EZ": "Simulated constant-maturity Bund 10Y total return",
        },
        "series": series,
        "stats": stats,
        "disclaimer": "SIMULATED DATA — FOR ANALYTICAL DEMONSTRATION. Constant-maturity construction, not a total-return index vendor.",
    }


@router.get("/risk")
def risk_api(market: str = "US", window: int = 60, maturity: str = "10Y", db: Session = Depends(get_db)):
    if window not in (30, 60, 90, 252):
        raise HTTPException(400, "window must be 30, 60, 90 or 252")
    y = Q.yield_frame(db, market, maturity)
    r = Q.return_frame(db, market, maturity)
    dy = y.diff()
    yvol = rolling_vol(dy.dropna(), window, 252)  # already in pp; treat as return-like
    rvol = rolling_vol(r.dropna(), window, 252)
    cum = (1 + r.dropna()).cumprod()
    var = historical_var(r.dropna(), 0.05)
    return {
        "market": Q.code(market),
        "window": window,
        "yield_vol": [{"date": i.date().isoformat(), "value": float(v)} for i, v in yvol.dropna().items()],
        "return_vol": [{"date": i.date().isoformat(), "value": float(v)} for i, v in rvol.dropna().items()],
        "drawdown": [{"date": i.date().isoformat(), "value": float(v)} for i, v in drawdown_series(cum).items()],
        "var_5pct_daily": var,
        "sharpe": sharpe(r),
        "max_drawdown": max_drawdown(cum),
        "note": "VaR is the 5% historical quantile of daily total returns in this sample — an estimate, not a guarantee.",
    }


@router.get("/correlation")
def correlation_api(
    window: str = "1Y",
    kind: str = "yield",
    db: Session = Depends(get_db),
):
    specs = [
        ("US", "10Y"),
        ("IN", "10Y"),
        ("UK", "10Y"),
        ("EZ", "10Y"),
        ("US", "2Y"),
        ("IN", "2Y"),
        ("UK", "2Y"),
        ("EZ", "2Y"),
    ]
    cols = {}
    for m, t in specs:
        s = Q.yield_frame(db, m, t)
        label = f"{m} {t}"
        if kind == "return":
            cols[label] = Q.return_frame(db, m, t if t != "2Y" else "2Y")
        elif kind == "change":
            cols[label] = s.diff()
        else:
            cols[label] = s
    df = pd.DataFrame(cols)
    win_map = {"30D": 30, "90D": 90, "1Y": 252, "3Y": 252 * 3, "5Y": 252 * 5}
    w = win_map.get(window.upper(), 252)
    tail = df.tail(w)
    matrix = corr_matrix(tail)
    # rolling US-IN 10Y for a companion chart
    rc = rolling_corr(df["US 10Y"].diff(), df["IN 10Y"].diff(), min(90, w))
    return {
        "kind": kind,
        "window": window,
        **matrix,
        "rolling_us_in": [{"date": i.date().isoformat(), "value": float(v)} for i, v in rc.dropna().items()],
        "note": "Correlation is an observed co-movement statistic. It does not prove transmission or causation.",
    }


@router.get("/scatter")
def scatter_api(x: str, y: str, db: Session = Depends(get_db)):
    """x,y like US:10Y or US:inflation or US:policy"""
    def parse(tok: str) -> pd.Series:
        mkt, var = tok.split(":")
        if var == "policy":
            return Q.policy_frame(db, mkt)
        if var in ("inflation", "gdp", "unemployment", "fx", "m2", "oil", "vix"):
            return Q.macro_frame(db, mkt, var)
        return Q.yield_frame(db, mkt, var)

    a = parse(x).resample("ME").last()
    b = parse(y).resample("ME").last()
    aligned = pd.concat([a, b], axis=1).dropna()
    aligned.columns = ["x", "y"]
    if len(aligned) < 8:
        raise HTTPException(400, "Not enough overlapping monthly observations.")
    X = np.vstack([aligned["x"], np.ones(len(aligned))]).T
    slope, intercept = np.linalg.lstsq(X, aligned["y"], rcond=None)[0]
    corr = float(aligned["x"].corr(aligned["y"]))
    r2 = corr**2
    return {
        "x": x,
        "y": y,
        "n": int(len(aligned)),
        "correlation": corr,
        "r_squared": float(r2),
        "slope": float(slope),
        "intercept": float(intercept),
        "points": [{"x": float(r.x), "y": float(r.y), "date": i.date().isoformat()} for i, r in aligned.iterrows()],
    }


@router.post("/regression")
def regression_api(body: dict, db: Session = Depends(get_db)):
    dep = body.get("dependent", "IN:10Y")
    inds = body.get("independents", ["US:10Y", "IN:policy", "IN:inflation"])
    diffs = body.get("differences", True)

    def parse(tok: str) -> pd.Series:
        mkt, var = tok.split(":")
        if var == "policy":
            s = Q.policy_frame(db, mkt)
        elif var in ("inflation", "gdp", "unemployment", "fx", "m2", "oil", "vix"):
            s = Q.macro_frame(db, mkt, var)
        else:
            s = Q.yield_frame(db, mkt, var)
        return s.resample("ME").last()

    y = parse(dep)
    X = pd.DataFrame({k: parse(k) for k in inds})
    if diffs:
        y = y.diff()
        X = X.diff()
    result = ols(y, X)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "regression failed"))
    result["dependent"] = dep
    result["independents"] = inds
    result["differences"] = diffs
    result["sample"] = "Monthly, DEMO series"
    return result


@router.get("/lags")
def lags_api(a: str = "IN:10Y", b: str = "US:10Y", db: Session = Depends(get_db)):
    def parse(tok: str) -> pd.Series:
        mkt, var = tok.split(":")
        return Q.yield_frame(db, mkt, var).diff()

    lags = [0, 1, 5, 10, 20, 30]
    rows = lag_correlations(parse(a), parse(b), lags)
    best = max(rows, key=lambda r: abs(r["correlation"] or 0))
    return {
        "a": a,
        "b": b,
        "lags": rows,
        "strongest": best,
        "label": "Observed relationship — not proof of causality",
        "interpretation": (
            f"Corr(Δ{a}_t, Δ{b}_{{t-k}}) is strongest at k={best['lag']} "
            f"({best['correlation']:.3f}) in this DEMO sample."
        ),
    }


@router.get("/macro")
def macro_api(market: str = "US", db: Session = Depends(get_db)):
    out = {}
    for ind in ("inflation", "gdp", "unemployment", "fx", "m2", "oil", "vix"):
        s = Q.macro_frame(db, market, ind)
        out[ind] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in s.items()]
    y2 = Q.yield_frame(db, market, "2Y").resample("ME").last()
    y10 = Q.yield_frame(db, market, "10Y").resample("ME").last()
    p = Q.policy_frame(db, market).resample("ME").last()
    out["y2"] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in y2.dropna().items()]
    out["y10"] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in y10.dropna().items()]
    out["policy"] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in p.dropna().items()]
    slope_df = pd.concat([y10.rename("y10"), y2.rename("y2")], axis=1).dropna()
    out["slope"] = [
        {"date": i.date().isoformat(), "value": float(r.y10 - r.y2)}
        for i, r in slope_df.iterrows()
    ]
    return {"market": Q.code(market), "series": out}


@router.post("/scenario")
def scenario_api(body: ScenarioRequest):
    return run_scenario(
        body.fed_bp,
        body.rbi_bp,
        body.boe_bp,
        body.ecb_bp,
        body.inflation_shock_pp,
        body.growth_shock_pp,
        body.risk_off,
    )


@router.post("/bond-lab")
def bond_lab(body: BondLabRequest):
    y = body.yield_rate
    p = bond_price(body.face, body.coupon_rate, y, body.maturity_years, body.frequency)
    mac = macaulay_duration(body.face, body.coupon_rate, y, body.maturity_years, body.frequency)
    mod = modified_duration(body.face, body.coupon_rate, y, body.maturity_years, body.frequency)
    conv = convexity(body.face, body.coupon_rate, y, body.maturity_years, body.frequency)
    dy = body.yield_shock_bp / 10000.0
    y2 = y + dy
    p_actual = bond_price(body.face, body.coupon_rate, y2, body.maturity_years, body.frequency)
    p_dur = p + duration_price_change(p, mod, dy, None)
    p_conv = p + duration_price_change(p, mod, dy, conv)
    curve = []
    for bp in range(-300, 301, 10):
        yy = y + bp / 10000.0
        if yy <= -0.005:
            continue
        curve.append(
            {
                "yield": yy * 100,
                "price": bond_price(body.face, body.coupon_rate, yy, body.maturity_years, body.frequency),
            }
        )
    return {
        "price": p,
        "current_yield": current_yield(body.face, body.coupon_rate, p),
        "macaulay": mac,
        "modified": mod,
        "convexity": conv,
        "shock_bp": body.yield_shock_bp,
        "actual_price": p_actual,
        "duration_approx": p_dur,
        "convexity_approx": p_conv,
        "duration_error": p_dur - p_actual,
        "convexity_error": p_conv - p_actual,
        "curve": curve,
        "note": "Bond prices and yields generally move inversely because the present value of fixed cash flows changes when the discount rate changes.",
    }


@router.get("/comparison")
def comparison(range: str = "5Y", db: Session = Depends(get_db)):
    end = _last_date(db)
    start = Q.window_start(end, range)
    rows = []
    names = ["Policy Rate", "10Y Yield", "2Y Yield", "10Y-2Y", "1Y Volatility", "5Y Return", "10Y Return", "Inflation", "GDP Growth", "Policy Direction"]
    matrix = {n: {} for n in names}
    series = {"y10": {}, "policy": {}, "slope": {}}
    for mkt in ("US", "IN", "UK", "EZ"):
        p = Q.policy_frame(db, mkt, start, end)
        y10 = Q.yield_frame(db, mkt, "10Y", start, end)
        y2 = Q.yield_frame(db, mkt, "2Y", start, end)
        r10 = Q.return_frame(db, mkt, "10Y")
        r10 = r10[r10.index >= pd.Timestamp(start)]
        inf = Q.macro_frame(db, mkt, "inflation")
        gdp = Q.macro_frame(db, mkt, "gdp")
        d90 = float((p.iloc[-1] - p.iloc[-63]) * 100) if len(p) > 63 else 0
        direction = "HIKING" if d90 >= 12 else "CUTTING" if d90 <= -12 else "HOLDING"
        vol = float(y10.diff().tail(252).std() * np.sqrt(252)) if len(y10) > 252 else None
        def cumul(s, years):
            sl = s.tail(252 * years)
            if sl.empty:
                return None
            return float((1 + sl).prod() - 1)
        matrix["Policy Rate"][mkt] = float(p.iloc[-1])
        matrix["10Y Yield"][mkt] = float(y10.iloc[-1])
        matrix["2Y Yield"][mkt] = float(y2.iloc[-1])
        matrix["10Y-2Y"][mkt] = float(y10.iloc[-1] - y2.iloc[-1])
        matrix["1Y Volatility"][mkt] = vol
        matrix["5Y Return"][mkt] = cumul(r10, 5)
        matrix["10Y Return"][mkt] = cumul(r10, 10) if len(r10) > 2000 else cumul(r10, 8)
        matrix["Inflation"][mkt] = None if inf.empty else float(inf.iloc[-1])
        matrix["GDP Growth"][mkt] = None if gdp.empty else float(gdp.iloc[-1])
        matrix["Policy Direction"][mkt] = direction
        series["y10"][mkt] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in y10.items()]
        series["policy"][mkt] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in p.items()]
        sl = y10 - y2
        series["slope"][mkt] = [{"date": i.date().isoformat(), "value": float(v)} for i, v in sl.dropna().items()]
        rc = rolling_corr(y10.diff(), Q.yield_frame(db, "US", "10Y", start, end).diff(), 90)
        rows.append({"market": mkt, "rolling_vs_us": [{"date": i.date().isoformat(), "value": float(v)} for i, v in rc.dropna().items()]})
    return {"matrix": matrix, "series": series, "rolling": rows}


@router.get("/regimes")
def regimes(market: str = "US", db: Session = Depends(get_db)):
    p = Q.policy_frame(db, market)
    y2 = Q.yield_frame(db, market, "2Y")
    y10 = Q.yield_frame(db, market, "10Y")
    r = Q.return_frame(db, market, "10Y")
    d90 = p.diff(63) * 100
    labels = d90.apply(lambda x: "HAWKISH" if x >= 25 else "DOVISH" if x <= -25 else "NEUTRAL")
    aligned = pd.concat([labels, y2, y10, r], axis=1).dropna()
    aligned.columns = ["regime", "y2", "y10", "ret"]
    out = []
    for name, g in aligned.groupby("regime"):
        out.append(
            {
                "regime": name,
                "n": int(len(g)),
                "avg_2y": float(g["y2"].mean()),
                "avg_10y": float(g["y10"].mean()),
                "avg_vol": float(g["ret"].std() * np.sqrt(252)),
                "avg_return_ann": float(g["ret"].mean() * 252),
            }
        )
    return {
        "market": Q.code(market),
        "rule": "HAWKISH if 90-session policy-rate change ≥ +25 bp; DOVISH if ≤ −25 bp; else NEUTRAL.",
        "regimes": out,
    }


@router.get("/methodology")
def methodology():
    return {
        "demo": True,
        "data": "All series are simulated with historically recognisable policy waypoints. Never cite as official prints.",
        "yields": "Nelson-Siegel: y(τ)=β0+β1(1−e^{−τ/λ})/(τ/λ)+β2[(1−e^{−τ/λ})/(τ/λ)−e^{−τ/λ}], λ=1.4.",
        "returns": "Constant-maturity: reprice a par-coupon bond each day; coupon accrual = y_{t-1} × Δt.",
        "duration": "Macaulay duration is the PV-weighted maturity of cash flows. Modified duration = Mac / (1+y/m).",
        "event_study": "Paths demeaned at t=0. Average is descriptive. No identification strategy is claimed.",
        "regression": "Monthly OLS on differences. Standard errors are classical — autocorrelation likely inflates t-stats.",
        "scenario": "Linear elasticities documented in analytics/scenario.py. ILLUSTRATIVE — NOT A FORECAST.",
        "regimes": "Transparent 90-session policy-rate threshold, not a Markov-switching model.",
    }


@router.get("/sources")
def sources(db: Session = Depends(get_db)):
    rows = db.query(DataSource).all()
    return [
        {
            "code": r.code,
            "name": r.name,
            "institution": r.institution,
            "variable": r.variable,
            "frequency": r.frequency,
            "date_range": r.date_range,
            "transformation": r.transformation,
            "methodology": r.methodology,
            "url": r.url,
            "demo": bool(r.demo),
        }
        for r in rows
    ]


@router.get("/guess-curve")
def guess_curve(db: Session = Depends(get_db)):
    """Unlabelled historical curve + later outcome for the teaching game."""
    puzzles = [
        (date(2019, 12, 31), date(2020, 6, 30), "Pre-COVID UST. What happened next?"),
        (date(2022, 3, 1), date(2022, 10, 31), "Hiking begins. Did the curve invert?"),
        (date(2022, 9, 20), date(2022, 10, 14), "UK — days around the mini-budget."),
        (date(2024, 8, 1), date(2025, 3, 1), "Easing starts. Bull-steepener or not?"),
    ]
    i = int(pd.Timestamp(_last_date(db)).day) % len(puzzles)
    a, b, q = puzzles[i]
    mkt = "UK" if a.year == 2022 and a.month == 9 else "US"
    before = Q.curve_on(db, mkt, a)
    after = Q.curve_on(db, mkt, b)
    d0 = before.pop("_date")
    d1 = after.pop("_date")
    return {
        "market": mkt,
        "question": q,
        "before_date": d0.isoformat(),
        "after_date": d1.isoformat(),
        "before": [{"maturity": k, "tenor_years": TENOR_YEARS[k], "yield_pct": before[k]} for k in TENOR_YEARS if k in before],
        "after": [{"maturity": k, "tenor_years": TENOR_YEARS[k], "yield_pct": after[k]} for k in TENOR_YEARS if k in after],
    }
