from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.formulas import interest_income
from app.models.entities import InvestmentOption
from app.treasury.engine import positions_at, reporting_meta, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


def investments(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    instrument: str = "mmf",
    amount: Optional[float] = None,
    horizon_days: int = 90,
) -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy)
    surplus = max(0.0, sim["totals"]["idle"])
    opts = db.query(InvestmentOption).all()
    chosen = next((o for o in opts if o.id == instrument), opts[0] if opts else None)
    deploy = surplus if amount is None else convert_to_inr(amount, reporting, fx)
    deploy = min(deploy, surplus)
    years = horizon_days / 365.0
    income = interest_income(deploy, chosen.yield_pct if chosen else 0.05, years) if chosen else 0
    table = []
    for o in opts:
        inc = interest_income(deploy, o.yield_pct, years)
        table.append(
            {
                "id": o.id,
                "name": o.name,
                "horizon_days": o.horizon_days,
                "yield_pct": o.yield_pct,
                "liquidity_score": o.liquidity_score,
                "income": convert_inr_cr(inc, reporting, fx),
                "note": o.risk_note,
            }
        )
    return {
        "meta": reporting_meta(reporting, fx),
        "label": "Illustrative treasury allocation.",
        "available_surplus": convert_inr_cr(surplus, reporting, fx),
        "deployed": convert_inr_cr(deploy, reporting, fx),
        "horizon_days": horizon_days,
        "expected_income": convert_inr_cr(income, reporting, fx),
        "opportunity_cost": convert_inr_cr(interest_income(surplus, 0.056, years) - income, reporting, fx),
        "liquidity_impact": "Investing surplus reduces idle cash but can reduce same-day optionality.",
        "options": table,
        "disclaimer": "Not a recommendation. Yields are simulated.",
    }


def convert_to_inr(amount: float, reporting: str, fx: dict[str, float]) -> float:
    if reporting == "INR":
        return amount
    rate = {"USD": fx.get("USDINR", 83), "GBP": fx.get("GBPINR", 106), "SGD": fx.get("SGDINR", 62)}.get(reporting, 1)
    return amount * rate / 10.0
