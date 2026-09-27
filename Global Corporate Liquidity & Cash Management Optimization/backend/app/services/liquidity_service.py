from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.formulas import cash_runway, liquidity_gap, mean
from app.models.entities import CashFlow, LiquidityPosition
from app.treasury.engine import PoolParams, positions_at, reporting_meta, serialize_position, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map, monthly_rows


def liquidity(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    country: Optional[str] = None,
    params: Optional[PoolParams] = None,
) -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy, params)
    mapped = [serialize_position(p, reporting, fx) for p in sim["positions"]]
    if country and country not in ("ALL", "GLOBAL"):
        mapped = [m for m in mapped if m["country"] == country]

    heat = []
    rows = monthly_rows(db, country if country not in ("ALL", "GLOBAL", None) else None, date(2024, 1, 31), AS_OF)
    for r in rows:
        gap = r.inr_closing - r.inr_min_cash
        heat.append(
            {
                "country": r.country,
                "period": r.period.isoformat()[:7],
                "surplus": convert_inr_cr(max(0, gap), reporting, fx),
                "deficit": convert_inr_cr(max(0, -gap), reporting, fx),
                "net": convert_inr_cr(gap, reporting, fx),
                "status": "surplus" if gap >= 0 else "deficit",
            }
        )

    t = sim["totals"]
    daily = mean([p.inr_outflows / 30.4 for p in sim["positions"]])
    gap_now = liquidity_gap(t["cash"], t["inflows"], t["outflows"], sum(p.inr_min for p in sim["positions"]))
    return {
        "meta": reporting_meta(reporting, fx),
        "positions": mapped,
        "heatmap": heat,
        "gap": convert_inr_cr(gap_now, reporting, fx),
        "runway_days": cash_runway(t["cash"], daily if daily else 1),
        "runway_note": "Cash Runway = Available Cash / Average Daily Outflow. Ignores restricted cash, undrawn facilities, and intra-month timing.",
        "totals": {k: convert_inr_cr(v, reporting, fx) if isinstance(v, float) else v for k, v in t.items()},
        "idle_ranking": sorted(mapped, key=lambda x: x["idle"], reverse=True),
        "formula": {
            "closing": "Opening + Inflows − Outflows",
            "excess": "Closing − Minimum Required Cash",
            "idle": "max(0, Closing − Operating Requirement − Invested)",
            "gap": "Available + Expected Inflows − Expected Outflows − Minimum Cash",
        },
    }


def forecast(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    country: Optional[str] = None,
) -> dict:
    """12-month liquidity forecast from as-of using seasonal last-year path × scenario."""
    from app.treasury.engine import scenario_params

    fx = latest_fx_map(db)
    sc = scenario_params(db, scenario)
    start = date(2025, 9, 30)
    end = date(2026, 8, 31)
    hist = monthly_rows(db, country if country not in ("ALL", "GLOBAL", None) else None, start, end)
    by_month: dict[str, dict] = {}
    for r in hist:
        key = r.period.strftime("%m")
        by_month.setdefault(key, {"inflows": 0.0, "outflows": 0.0, "closing": 0.0, "min": 0.0})
        by_month[key]["inflows"] += r.inr_inflows
        by_month[key]["outflows"] += r.inr_outflows
        by_month[key]["closing"] += r.inr_closing
        by_month[key]["min"] += r.inr_min_cash

    # Build 12 months starting Oct 2026 using 2025-26 seasonality
    months = ["10", "11", "12", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
    years = [2026, 2026, 2026, 2027, 2027, 2027, 2027, 2027, 2027, 2027, 2027, 2027]
    series = []
    cash = sum(by_month.get("09", {"closing": 0})["closing"] for _ in [0]) or sum(
        r.inr_closing for r in monthly_rows(db, None, AS_OF, AS_OF)
    )
    for i, (m, y) in enumerate(zip(months, years)):
        base = by_month.get(m, {"inflows": 80, "outflows": 78, "min": 40})
        inf = base["inflows"] * sc["collection_factor"]
        out = base["outflows"] * sc["outflow_factor"]
        cash = cash + inf - out
        mn = base["min"]
        # Uncertainty band widens through the horizon.
        band = 0.04 + i * 0.008
        opt_cash = cash * (1.04 + i * 0.004)
        stress_cash = cash * (0.90 - i * 0.006)
        series.append(
            {
                "period": f"{y}-{m}",
                "inflows": convert_inr_cr(inf, reporting, fx),
                "outflows": convert_inr_cr(out, reporting, fx),
                "closing": convert_inr_cr(cash, reporting, fx),
                "min_cash": convert_inr_cr(mn, reporting, fx),
                "optimistic": convert_inr_cr(opt_cash, reporting, fx),
                "stressed": convert_inr_cr(stress_cash, reporting, fx),
                "band": band,
                "surplus": convert_inr_cr(max(0, cash - mn), reporting, fx),
                "deficit": convert_inr_cr(max(0, mn - cash), reporting, fx),
            }
        )
    return {"meta": reporting_meta(reporting, fx), "horizon": series, "scenario": scenario}
