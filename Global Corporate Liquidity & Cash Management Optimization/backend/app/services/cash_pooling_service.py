from typing import Optional

from sqlalchemy.orm import Session

from app.treasury.engine import PoolParams, compare_strategies, positions_at, reporting_meta, serialize_position, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


def pooling(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "hybrid",
    members: Optional[list[str]] = None,
    min_buffer_mult: float = 1.0,
    transfer_threshold: float = 5.0,
    investment_threshold: float = 22.0,
    borrowing_threshold: float = 2.0,
) -> dict:
    fx = latest_fx_map(db)
    params = PoolParams(
        members=members or ["IN", "US", "UK", "SG"],
        min_buffer_mult=min_buffer_mult,
        transfer_threshold=transfer_threshold,
        investment_threshold=investment_threshold,
        borrowing_threshold=borrowing_threshold,
    )
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy, params)
    baseline = simulate_strategy(pos, "none", params)
    t = sim["totals"]
    b = baseline["totals"]
    return {
        "meta": reporting_meta(reporting, fx),
        "strategy": strategy,
        "positions": [serialize_position(p, reporting, fx) for p in sim["positions"]],
        "transfers": sim["transfers"],
        "notes": sim["notes"],
        "totals": {
            "idle": convert_inr_cr(t["idle"], reporting, fx),
            "funding": convert_inr_cr(t["funding"], reporting, fx),
            "interest_income": convert_inr_cr(t["interest_income"], reporting, fx),
            "interest_expense": convert_inr_cr(t["interest_expense"], reporting, fx),
            "fx": convert_inr_cr(t["fx"], reporting, fx),
            "efficiency": t["efficiency"],
            "benefit": convert_inr_cr(t["pooling_benefit"], reporting, fx),
            "transfers": convert_inr_cr(sum(x["amount_inr"] for x in sim["transfers"]), reporting, fx),
        },
        "baseline": {
            "idle": convert_inr_cr(b["idle"], reporting, fx),
            "funding": convert_inr_cr(b["funding"], reporting, fx),
            "interest_expense": convert_inr_cr(b["interest_expense"], reporting, fx),
        },
        "tradeoff": _tradeoff(strategy, sim),
        "explanations": {
            "none": "No pooling — each legal entity manages its own cash. Simple, fragmented, and often expensive.",
            "physical": "Physical pooling — cash is actually transferred to a header account. Highest operational and FX complexity.",
            "notional": "Notional pooling — balances remain separate but are considered together for interest, subject to banking arrangements.",
            "hybrid": "Hybrid — physical sweeps for material gaps; notional interest on the residual. Usually the best simulated balance.",
        },
        "feasibility": "Real-world feasibility depends on jurisdiction, banking structure, tax rules, capital controls, and legal arrangements.",
        "params": sim["params"],
    }


def _tradeoff(strategy: str, sim: dict) -> str:
    if strategy == "none":
        return "India can sit on surplus while Singapore borrows. Group idle cash stays high."
    if sim["transfers"]:
        t0 = sim["transfers"][0]
        return (
            f"{t0['from']} surplus funds {t0['to']}. {t0['to']} avoids external borrowing; "
            f"{t0['from']} earns less idle cash. Group financing cost falls."
        )
    if strategy == "notional":
        return "Interest is netted, but cash is still trapped in legal entities. Idle cash barely moves."
    return "Residual balances remain local after material gaps are closed."
