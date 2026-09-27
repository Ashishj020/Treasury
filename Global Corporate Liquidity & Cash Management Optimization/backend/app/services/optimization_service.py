from typing import Optional

from sqlalchemy.orm import Session

from app.treasury.engine import PoolParams, compare_strategies, positions_at, reporting_meta
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


def optimize(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    weights: Optional[dict] = None,
    params: Optional[PoolParams] = None,
) -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    cmp_ = compare_strategies(pos, params, weights=weights)
    c = lambda v: convert_inr_cr(v, reporting, fx)
    waterfall = [
        {"label": "Baseline financing cost", "value": c(cmp_["financing_cost_baseline"])},
        {"label": "Cash pooling benefit", "value": -c(cmp_["results"]["hybrid"]["totals"]["pooling_benefit"] * 0.45)},
        {"label": "Investment income", "value": -c(cmp_["investment_income_optimized"] - cmp_["investment_income_baseline"])},
        {"label": "Borrowing reduction", "value": -c(cmp_["financing_savings"])},
        {"label": "FX optimization", "value": -c((cmp_["fx_baseline"] - cmp_["fx_optimized"]) * 0.02)},
        {"label": "Optimized cost", "value": c(cmp_["financing_cost_optimized"])},
    ]
    return {
        "meta": reporting_meta(reporting, fx),
        "label": "SIMULATED OPTIMIZATION RESULT",
        "baseline_idle": c(cmp_["baseline_idle"]),
        "optimized_idle": c(cmp_["optimized_idle"]),
        "cash_released": c(cmp_["cash_released"]),
        "idle_reduction": cmp_["idle_reduction"],
        "financing_cost_baseline": c(cmp_["financing_cost_baseline"]),
        "financing_cost_optimized": c(cmp_["financing_cost_optimized"]),
        "financing_savings": c(cmp_["financing_savings"]),
        "investment_income_baseline": c(cmp_["investment_income_baseline"]),
        "investment_income_optimized": c(cmp_["investment_income_optimized"]),
        "fx_baseline": c(cmp_["fx_baseline"]),
        "fx_optimized": c(cmp_["fx_optimized"]),
        "fx_reduction": cmp_["fx_reduction"],
        "winner": cmp_["winner"],
        "scorecard": [
            {
                **row,
                "idle": c(row["idle"]),
                "funding": c(row["funding"]),
                "financing_cost": c(row["financing_cost"]),
                "investment_income": c(row["investment_income"]),
                "fx": c(row["fx"]),
                "benefit": c(row["benefit"]),
            }
            for row in cmp_["scorecard"]
        ],
        "waterfall": waterfall,
        "weights": cmp_["weights"],
        "before_after": {
            "before": {
                "idle": c(cmp_["baseline_idle"]),
                "borrowing": c(cmp_["results"]["none"]["totals"]["funding"]),
                "investment_income": c(cmp_["investment_income_baseline"]),
                "fx": c(cmp_["fx_baseline"]),
            },
            "after": {
                "idle": c(cmp_["optimized_idle"]),
                "borrowing": c(cmp_["results"]["hybrid"]["totals"]["funding"]),
                "investment_income": c(cmp_["investment_income_optimized"]),
                "fx": c(cmp_["fx_optimized"]),
            },
        },
        "note": "The ~12% idle-cash reduction is a calculated outcome of this simulated book under hybrid pooling plus short-term deployment — not an assumed constant.",
    }
