from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.formulas import borrowing_cost
from app.models.entities import BorrowingFacility
from app.treasury.engine import positions_at, reporting_meta, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map
from app.services.investment_service import convert_to_inr


def borrowing(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    facility: str = "rcf_in",
    amount: Optional[float] = None,
    tenor_days: int = 90,
) -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    none = simulate_strategy(pos, "none")
    pooled = simulate_strategy(pos, strategy)
    need = none["totals"]["funding"]
    covered = max(0.0, need - pooled["totals"]["funding"])
    facs = db.query(BorrowingFacility).all()
    chosen = next((f for f in facs if f.id == facility), facs[0])
    draw = convert_to_inr(amount, reporting, fx) if amount is not None else need
    years = tenor_days / 365.0
    cost = borrowing_cost(draw, chosen.rate_pct, years)
    table = []
    for f in facs:
        local_need = draw
        c = borrowing_cost(local_need, f.rate_pct, years)
        table.append(
            {
                "id": f.id,
                "name": f.name,
                "currency": f.currency,
                "country": f.country,
                "rate_pct": f.rate_pct,
                "tenor_days": f.tenor_days,
                "limit": f.limit_local,
                "drawn": f.drawn_local,
                "cost": convert_inr_cr(c, reporting, fx),
                "notes": f.notes,
            }
        )
    ic_cost = borrowing_cost(draw, 0.071, years)
    pool_cost = pooled["totals"]["interest_expense"] * (tenor_days / 365)
    return {
        "meta": reporting_meta(reporting, fx),
        "funding_need": convert_inr_cr(need, reporting, fx),
        "avoided_by_pooling": convert_inr_cr(covered, reporting, fx),
        "draw": convert_inr_cr(draw, reporting, fx),
        "interest_cost": convert_inr_cr(cost, reporting, fx),
        "effective_cost_pct": chosen.rate_pct,
        "tenor_days": tenor_days,
        "facilities": table,
        "compare": [
            {
                "path": "Borrow locally",
                "cost": convert_inr_cr(cost, reporting, fx),
                "note": "Simple. Leaves surplus idle in other countries.",
            },
            {
                "path": "Pool excess cash elsewhere",
                "cost": convert_inr_cr(pool_cost, reporting, fx),
                "note": "Uses India/UK surplus before drawing a revolver.",
            },
            {
                "path": "Intercompany funding",
                "cost": convert_inr_cr(ic_cost, reporting, fx),
                "note": "Transfer-pricing, thin-cap and withholding tax still apply in real life.",
            },
        ],
        "formula": "Interest Expense = Borrowing Amount × Interest Rate × Time",
    }
