from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import (
    borrowing_service,
    cash_flow_service,
    cash_pooling_service,
    fx_service,
    insights_service,
    investment_service,
    liquidity_service,
    optimization_service,
    scenario_service,
    strategy_service,
    working_capital_service,
)
from app.treasury.engine import PoolParams


router = APIRouter(prefix="/api")


class ScenarioBody(BaseModel):
    scenario: str = "stressed"
    reporting: str = "INR"
    strategy: str = "none"
    collection_factor: Optional[float] = None
    outflow_factor: Optional[float] = None
    rate_shift_bp: Optional[float] = None
    fx_inr_shock: Optional[float] = None
    receivable_delay_days: Optional[int] = None
    opex_factor: Optional[float] = None


class OptimizeBody(BaseModel):
    reporting: str = "INR"
    scenario: str = "base"
    liquidity: float = 0.4
    cost: float = 0.3
    fx: float = 0.2
    return_w: float = Field(0.1, alias="return")
    members: Optional[list[str]] = None
    transfer_threshold: float = 5.0
    investment_threshold: float = 22.0
    borrowing_threshold: float = 2.0
    min_buffer_mult: float = 1.0

    model_config = {"populate_by_name": True}


class ResearchBody(BaseModel):
    country: str = "ALL"
    currency: str = "INR"
    scenario: str = "base"
    strategy: str = "hybrid"
    metric: str = "idle"
    question: Optional[str] = None


class TreasurerGameBody(BaseModel):
    choice: str = "pool"
    amount: float = 100.0
    reporting: str = "INR"


def _pool_params(
    members: Optional[str],
    transfer_threshold: float,
    investment_threshold: float,
    borrowing_threshold: float,
    min_buffer_mult: float,
) -> PoolParams:
    mem = members.split(",") if members else ["IN", "US", "UK", "SG"]
    mem = [m.strip() for m in mem if m.strip()]
    return PoolParams(
        members=mem,
        transfer_threshold=transfer_threshold,
        investment_threshold=investment_threshold,
        borrowing_threshold=borrowing_threshold,
        min_buffer_mult=min_buffer_mult,
    )


@router.get("/countries")
def get_countries(db: Session = Depends(get_db)):
    return strategy_service.countries(db)


@router.get("/cash-flows")
def get_cash_flows(
    country: Optional[str] = None,
    reporting: str = "INR",
    scenario: str = "base",
    granularity: str = "month",
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return cash_flow_service.cash_flows(db, country, start, end, reporting, scenario, granularity)


@router.get("/overview")
def get_overview(
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    country: str = "ALL",
    members: Optional[str] = None,
    transfer_threshold: float = 5.0,
    investment_threshold: float = 22.0,
    borrowing_threshold: float = 2.0,
    min_buffer_mult: float = 1.0,
    db: Session = Depends(get_db),
):
    params = _pool_params(members, transfer_threshold, investment_threshold, borrowing_threshold, min_buffer_mult)
    return cash_flow_service.overview(db, reporting, scenario, strategy, country, params)


@router.get("/liquidity")
def get_liquidity(
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    country: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return liquidity_service.liquidity(db, reporting, scenario, strategy, country)


@router.get("/forecast")
def get_forecast(reporting: str = "INR", scenario: str = "base", country: Optional[str] = None, db: Session = Depends(get_db)):
    return liquidity_service.forecast(db, reporting, scenario, country)


@router.get("/working-capital")
def get_wc(
    reporting: str = "INR",
    country: Optional[str] = None,
    dso: Optional[float] = None,
    dpo: Optional[float] = None,
    inventory_days: Optional[float] = None,
    db: Session = Depends(get_db),
):
    return working_capital_service.working_capital_pack(db, reporting, country, dso, dpo, inventory_days)


@router.get("/receivables")
def get_ar(reporting: str = "INR", country: Optional[str] = None, db: Session = Depends(get_db)):
    return working_capital_service.receivables(db, reporting, country)


@router.get("/payables")
def get_ap(reporting: str = "INR", country: Optional[str] = None, timing: str = "terms", db: Session = Depends(get_db)):
    return working_capital_service.payables(db, reporting, country, timing)


@router.get("/fx")
def get_fx(
    reporting: str = "INR",
    scenario: str = "base",
    hedge_ratio: float = 0.5,
    hedge_style: str = "partial",
    usd_inr: Optional[float] = None,
    db: Session = Depends(get_db),
):
    return fx_service.fx_pack(db, reporting, scenario, hedge_ratio, hedge_style, usd_inr)


@router.get("/investments")
def get_investments(
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    instrument: str = "mmf",
    amount: Optional[float] = None,
    horizon_days: int = 90,
    db: Session = Depends(get_db),
):
    return investment_service.investments(db, reporting, scenario, strategy, instrument, amount, horizon_days)


@router.get("/borrowing")
def get_borrowing(
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    facility: str = "rcf_in",
    amount: Optional[float] = None,
    tenor_days: int = 90,
    db: Session = Depends(get_db),
):
    return borrowing_service.borrowing(db, reporting, scenario, strategy, facility, amount, tenor_days)


@router.get("/pooling")
def get_pooling(
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "hybrid",
    members: Optional[str] = None,
    transfer_threshold: float = 5.0,
    investment_threshold: float = 22.0,
    borrowing_threshold: float = 2.0,
    min_buffer_mult: float = 1.0,
    db: Session = Depends(get_db),
):
    mem = members.split(",") if members else None
    return cash_pooling_service.pooling(
        db,
        reporting,
        scenario,
        strategy,
        mem,
        min_buffer_mult,
        transfer_threshold,
        investment_threshold,
        borrowing_threshold,
    )


@router.post("/scenario")
def post_scenario(body: ScenarioBody, db: Session = Depends(get_db)):
    overrides = {
        "collection_factor": body.collection_factor,
        "outflow_factor": body.outflow_factor,
        "rate_shift_bp": body.rate_shift_bp,
        "fx_inr_shock": body.fx_inr_shock,
        "receivable_delay_days": body.receivable_delay_days,
        "opex_factor": body.opex_factor,
    }
    return scenario_service.run_scenario(db, body.reporting, body.scenario, overrides, body.strategy)


@router.post("/optimize")
def post_optimize(body: OptimizeBody, db: Session = Depends(get_db)):
    weights = {"liquidity": body.liquidity, "cost": body.cost, "fx": body.fx, "return": body.return_w}
    params = PoolParams(
        members=body.members or ["IN", "US", "UK", "SG"],
        transfer_threshold=body.transfer_threshold,
        investment_threshold=body.investment_threshold,
        borrowing_threshold=body.borrowing_threshold,
        min_buffer_mult=body.min_buffer_mult,
    )
    return optimization_service.optimize(db, body.reporting, body.scenario, weights, params)


@router.get("/strategy-comparison")
def get_strategy(reporting: str = "INR", scenario: str = "base", db: Session = Depends(get_db)):
    return strategy_service.strategy_pack(db, reporting, scenario)


@router.get("/insights")
def get_insights(reporting: str = "INR", scenario: str = "base", db: Session = Depends(get_db)):
    return strategy_service.strategy_pack(db, reporting, scenario)


@router.get("/methodology")
def get_methodology():
    return strategy_service.methodology()


@router.get("/matrix")
def get_matrix(reporting: str = "INR", scenario: str = "base", strategy: str = "none", db: Session = Depends(get_db)):
    return insights_service.matrix(db, reporting, scenario, strategy)


@router.get("/concentration")
def get_concentration(reporting: str = "INR", db: Session = Depends(get_db)):
    return insights_service.concentration(db, reporting)


@router.get("/country/{code}")
def get_country(code: str, reporting: str = "INR", scenario: str = "base", strategy: str = "none", db: Session = Depends(get_db)):
    return insights_service.country_dashboard(db, code.upper(), reporting, scenario, strategy)


@router.get("/sankey")
def get_sankey(reporting: str = "INR", strategy: str = "hybrid", db: Session = Depends(get_db)):
    return insights_service.sankey(db, reporting, strategy)


@router.get("/events")
def get_events(month: Optional[str] = None, db: Session = Depends(get_db)):
    return strategy_service.events(db, month)


@router.post("/research")
def post_research(body: ResearchBody, db: Session = Depends(get_db)):
    return strategy_service.research(body.model_dump(), db)


@router.post("/game")
def post_game(body: TreasurerGameBody, db: Session = Depends(get_db)):
    """Educational mini-sim: deploy ₹100Cr excess. Not advice."""
    fx = latest_fx_map(db)
    amount = body.amount if body.reporting == "INR" else body.amount
    # Consequences on stylised 0-100 scores
    paths = {
        "idle": {"liquidity": 88, "return": 12, "cost": 40, "fx": 55, "note": "Safest optionality. Cash earns almost nothing and may sit in the wrong country."},
        "invest": {"liquidity": 62, "return": 78, "cost": 48, "fx": 50, "note": "Return rises. Same-day optionality falls. Still does not fix a Singapore deficit."},
        "pool": {"liquidity": 84, "return": 44, "cost": 72, "fx": 48, "note": "Surplus funds the deficit entity. Borrowing falls. Cross-border FX and legal rails appear."},
        "borrow": {"liquidity": 70, "return": 28, "cost": 86, "fx": 58, "note": "Use the ₹100Cr to repay drawn credit. Financing cost drops; investment income is forgone."},
    }
    key = body.choice if body.choice in paths else "pool"
    result = paths[key]
    return {
        "choice": key,
        "amount": amount,
        "scores": result,
        "title": "Your Treasury Strategy",
        "disclaimer": "Educational simulation on a stylised ₹100Cr sleeve. Not financial advice.",
        "meta": reporting_meta(body.reporting, fx),
    }


# local imports used in game
from app.treasury.engine import reporting_meta
from app.utils.fx import latest_fx_map
