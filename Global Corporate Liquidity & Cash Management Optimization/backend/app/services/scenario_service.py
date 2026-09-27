from sqlalchemy.orm import Session

from app.analytics.formulas import cash_runway
from app.treasury.engine import PoolParams, positions_at, reporting_meta, scenario_params, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


def run_scenario(
    db: Session,
    reporting: str = "INR",
    scenario: str = "stressed",
    overrides: dict | None = None,
    strategy: str = "none",
) -> dict:
    fx = latest_fx_map(db)
    sc = scenario_params(db, scenario, overrides)
    pos = positions_at(db, AS_OF, scenario, overrides)
    sim = simulate_strategy(pos, strategy, PoolParams(), sc["rate_shift_bp"])
    base_pos = positions_at(db, AS_OF, "base")
    base = simulate_strategy(base_pos, "none")
    t = sim["totals"]
    b = base["totals"]
    min_buffer = sum(p.inr_min for p in sim["positions"])
    lowest = t["cash"] - t["outflows"] * 0.35
    breach = lowest < min_buffer * 0.85
    daily = t["outflows"] / 30.4
    return {
        "meta": reporting_meta(reporting, fx),
        "scenario": scenario,
        "assumptions": sc,
        "before": {
            "cash": convert_inr_cr(b["cash"], reporting, fx),
            "idle": convert_inr_cr(b["idle"], reporting, fx),
            "funding": convert_inr_cr(b["funding"], reporting, fx),
            "financing": convert_inr_cr(b["interest_expense"], reporting, fx),
            "fx": convert_inr_cr(b["fx"], reporting, fx),
        },
        "after": {
            "cash": convert_inr_cr(t["cash"], reporting, fx),
            "idle": convert_inr_cr(t["idle"], reporting, fx),
            "funding": convert_inr_cr(t["funding"], reporting, fx),
            "financing": convert_inr_cr(t["interest_expense"], reporting, fx),
            "fx": convert_inr_cr(t["fx"], reporting, fx),
        },
        "survival": {
            "min_buffer": convert_inr_cr(min_buffer, reporting, fx),
            "projected_low": convert_inr_cr(lowest, reporting, fx),
            "breach": breach,
            "status": "BUFFER BREACH" if breach else "BUFFER HOLDS",
            "runway_days": cash_runway(t["cash"], daily if daily else 1),
        },
        "suggestions": _suggestions(breach, t, b),
        "disclaimer": "Analytical suggestions for the simulated book. Not financial advice.",
    }


def _suggestions(breach: bool, t: dict, b: dict) -> list[str]:
    out = []
    if breach:
        out.append("Prioritize liquidity preservation over investment return.")
        out.append("Increase the liquidity buffer and delay discretionary investment.")
        out.append("Draw the revolving credit facility only after pooling surplus.")
    if t["funding"] > b["funding"]:
        out.append("Use the cash pool before borrowing locally in the deficit entity.")
    if t["idle"] > 20:
        out.append("Accelerate collections. A 5-day DSO cut releases working-capital cash.")
    out.append("Review natural-offset opportunities before buying FX forwards.")
    return out
