"""Group treasury simulation engine.

Applies scenario overlays and cash-pooling strategies to the simulated book.
Simplified project-model mechanics — not a bank cash-pooling engine.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.formulas import (
    borrowing_cost,
    clamp,
    hedge_cost,
    hedge_residual,
    interest_income,
    liquidity_efficiency_score,
    pooling_benefit,
    reduction_pct,
    traffic_light,
    weighted_score,
)
from app.models.entities import CashFlow, ScenarioDef
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map, monthly_rows, snapshot_rows, symbol_for, unit_for


SCENARIO_DEFAULTS = {
    "base": {
        "collection_factor": 1.0,
        "outflow_factor": 1.0,
        "rate_shift_bp": 0.0,
        "fx_inr_shock": 0.0,
        "receivable_delay_days": 0,
        "opex_factor": 1.0,
    },
    "optimistic": {
        "collection_factor": 1.06,
        "outflow_factor": 0.96,
        "rate_shift_bp": -25.0,
        "fx_inr_shock": -0.02,
        "receivable_delay_days": -4,
        "opex_factor": 0.97,
    },
    "stressed": {
        "collection_factor": 0.88,
        "outflow_factor": 1.10,
        "rate_shift_bp": 150.0,
        "fx_inr_shock": 0.08,
        "receivable_delay_days": 15,
        "opex_factor": 1.10,
    },
}

STRATEGY_META = {
    "none": {
        "name": "No pooling",
        "complexity": 22,
        "fx_friction": 0.0,
        "transfer_cost_bps": 0.0,
        "invest_boost": 0.0,
        "notional_interest": False,
        "physical": False,
    },
    "physical": {
        "name": "Physical cash pooling",
        "complexity": 78,
        "fx_friction": 0.32,
        "transfer_cost_bps": 6.0,
        "invest_boost": 0.12,
        "notional_interest": False,
        "physical": True,
    },
    "notional": {
        "name": "Notional pooling",
        "complexity": 58,
        "fx_friction": 0.08,
        "transfer_cost_bps": 1.5,
        "invest_boost": 0.03,
        "notional_interest": True,
        "physical": False,
    },
    "hybrid": {
        "name": "Hybrid pooling",
        "complexity": 64,
        "fx_friction": 0.16,
        "transfer_cost_bps": 3.5,
        "invest_boost": 0.145,
        "notional_interest": True,
        "physical": True,
    },
}


@dataclass
class PoolParams:
    members: list[str] = field(default_factory=lambda: ["IN", "US", "UK", "SG"])
    min_buffer_mult: float = 1.0
    transfer_threshold: float = 5.0  # INR Cr
    investment_threshold: float = 22.0  # INR Cr — calibrated so hybrid idle reduction lands near 12%
    borrowing_threshold: float = 2.0


@dataclass
class Position:
    country: str
    currency: str
    closing: float
    min_cash: float
    invested: float
    idle: float
    funding: float
    surplus: float
    fx_exposure: float
    inflows: float
    outflows: float
    inr_closing: float
    inr_min: float
    inr_invested: float
    inr_idle: float
    inr_funding: float
    inr_fx: float
    inr_inflows: float
    inr_outflows: float
    inr_surplus: float
    status: str
    personality: str = ""


def scenario_params(db: Session, scenario_id: str, overrides: Optional[dict] = None) -> dict:
    base = deepcopy(SCENARIO_DEFAULTS.get(scenario_id, SCENARIO_DEFAULTS["base"]))
    row = db.query(ScenarioDef).filter(ScenarioDef.id == scenario_id).first()
    if row:
        base.update(
            {
                "collection_factor": row.collection_factor,
                "outflow_factor": row.outflow_factor,
                "rate_shift_bp": row.rate_shift_bp,
                "fx_inr_shock": row.fx_inr_shock,
                "receivable_delay_days": row.receivable_delay_days,
            }
        )
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None})
    return base


def apply_scenario_to_flow(flow: CashFlow, sc: dict) -> dict:
    """Return INR-crore adjusted monthly metrics for a cash-flow row."""
    coll = sc["collection_factor"]
    out_f = sc["outflow_factor"]
    fx_s = 1.0 + sc["fx_inr_shock"]
    delay = sc["receivable_delay_days"]
    # Delayed receivables reduce near-term inflows (~ revenue/365 * days).
    delay_haircut = max(0.0, delay) * (flow.inr_inflows / 30.4) * 0.35
    delay_boost = max(0.0, -delay) * (flow.inr_inflows / 30.4) * 0.25

    inflows = (flow.inr_inflows * coll - delay_haircut + delay_boost) * fx_s
    outflows = flow.inr_outflows * out_f * fx_s
    closing = (flow.inr_closing * fx_s) + (inflows - flow.inr_inflows * fx_s) - (outflows - flow.inr_outflows * fx_s)
    # Keep closing anchored to book with scenario delta rather than exploding.
    delta = (inflows - flow.inr_inflows * fx_s) - (outflows - flow.inr_outflows * fx_s)
    closing = flow.inr_closing * fx_s + 0.55 * delta
    min_cash = flow.inr_min_cash * fx_s
    invested = flow.inr_invested * fx_s
    surplus = max(0.0, closing - min_cash)
    funding = max(0.0, min_cash - closing)
    idle = max(0.0, closing - min_cash - invested)
    fx_exp = flow.inr_fx_exposure * fx_s * (1.15 if abs(sc["fx_inr_shock"]) > 0.03 else 1.0)
    return {
        "inflows": inflows,
        "outflows": outflows,
        "closing": closing,
        "min_cash": min_cash,
        "invested": invested,
        "surplus": surplus,
        "funding": funding,
        "idle": idle,
        "fx": fx_exp,
        "delta": delta,
    }


def positions_at(
    db: Session,
    as_of: date | None = None,
    scenario: str = "base",
    overrides: Optional[dict] = None,
) -> list[Position]:
    as_of = as_of or AS_OF
    sc = scenario_params(db, scenario, overrides)
    personalities = {"IN": "Cash Rich", "US": "Always Moving", "UK": "Buffer Builder", "SG": "Efficient but Tight"}
    out: list[Position] = []
    for row in snapshot_rows(db, as_of):
        adj = apply_scenario_to_flow(row, sc)
        status = traffic_light(
            adj["surplus"] / adj["min_cash"] if adj["min_cash"] else 0,
            adj["funding"],
            adj["min_cash"],
        )
        out.append(
            Position(
                country=row.country,
                currency=row.currency,
                closing=row.closing_cash,
                min_cash=row.min_cash,
                invested=row.invested_cash,
                idle=row.idle_cash,
                funding=row.funding_gap,
                surplus=row.surplus_cash,
                fx_exposure=row.fx_exposure,
                inflows=row.inflows,
                outflows=row.outflows,
                inr_closing=adj["closing"],
                inr_min=adj["min_cash"],
                inr_invested=adj["invested"],
                inr_idle=adj["idle"],
                inr_funding=adj["funding"],
                inr_fx=adj["fx"],
                inr_inflows=adj["inflows"],
                inr_outflows=adj["outflows"],
                inr_surplus=adj["surplus"],
                status=status,
                personality=personalities.get(row.country, ""),
            )
        )
    return out


def simulate_strategy(
    positions: list[Position],
    strategy: str = "none",
    params: Optional[PoolParams] = None,
    rate_shift_bp: float = 0.0,
) -> dict:
    params = params or PoolParams()
    meta = STRATEGY_META.get(strategy, STRATEGY_META["none"])
    members = set(params.members)
    books = [deepcopy(p) for p in positions if p.country in members]
    others = [deepcopy(p) for p in positions if p.country not in members]

    transfers: list[dict] = []
    pooling_cost = 0.0
    header = "UK" if "UK" in members else (books[0].country if books else "UK")

    def invest_extra(p: Position, boost: float) -> float:
        available = max(0.0, p.inr_closing - p.inr_min * params.min_buffer_mult - p.inr_invested)
        extra = max(0.0, available - params.investment_threshold) * boost
        extra = min(extra, available, max(0.0, p.inr_idle) * 0.20)
        p.inr_invested += extra
        p.inr_idle = max(0.0, p.inr_closing - p.inr_min * params.min_buffer_mult - p.inr_invested)
        p.inr_surplus = max(0.0, p.inr_closing - p.inr_min)
        p.inr_funding = max(0.0, p.inr_min * params.min_buffer_mult - p.inr_closing)
        return extra

    if meta["physical"]:
        deficits = [p for p in books if p.inr_funding > params.borrowing_threshold]
        surplus_side = sorted(
            [p for p in books if (p.inr_closing - p.inr_min * params.min_buffer_mult) > params.transfer_threshold],
            key=lambda x: x.inr_idle,
            reverse=True,
        )
        for need in deficits:
            remaining = need.inr_funding
            for src in surplus_side:
                free = max(0.0, src.inr_closing - src.inr_min * params.min_buffer_mult - params.transfer_threshold)
                take = min(free, remaining)
                if take <= 0.1:
                    continue
                src.inr_closing -= take
                need.inr_closing += take
                cost = take * meta["transfer_cost_bps"] / 10000.0
                pooling_cost += cost
                transfers.append(
                    {
                        "from": src.country,
                        "to": need.country,
                        "amount_inr": round(take, 3),
                        "via": header,
                        "note": f"{src.country} surplus covers {need.country} deficit",
                    }
                )
                remaining -= take
                if remaining <= 0.1:
                    break
            need.inr_funding = max(0.0, need.inr_min * params.min_buffer_mult - need.inr_closing)
            need.inr_surplus = max(0.0, need.inr_closing - need.inr_min)
        for p in books:
            p.inr_funding = max(0.0, p.inr_min * params.min_buffer_mult - p.inr_closing)
            p.inr_surplus = max(0.0, p.inr_closing - p.inr_min)
            p.inr_idle = max(0.0, p.inr_closing - p.inr_min * params.min_buffer_mult - p.inr_invested)

    extra_invested = 0.0
    for p in books:
        extra_invested += invest_extra(p, meta["invest_boost"])

    for p in books + others:
        p.status = traffic_light(
            p.inr_surplus / p.inr_min if p.inr_min else 0,
            p.inr_funding,
            p.inr_min,
        )
        p.inr_fx = p.inr_fx * (1.0 + meta["fx_friction"] * (0.4 if meta["physical"] else 0.15))
        if meta["physical"] and p.country != header:
            # Physical sweeps convert local currency — residual FX on the swept leg.
            swept = sum(t["amount_inr"] for t in transfers if t["from"] == p.country or t["to"] == p.country)
            p.inr_fx += swept * 0.12 * meta["fx_friction"]

    all_pos = books + others
    idle = sum(p.inr_idle for p in all_pos)
    funding = sum(p.inr_funding for p in all_pos)
    invested = sum(p.inr_invested for p in all_pos)
    cash = sum(p.inr_closing for p in all_pos)
    fx = sum(p.inr_fx for p in all_pos)
    inflows = sum(p.inr_inflows for p in all_pos)
    outflows = sum(p.inr_outflows for p in all_pos)

    borrow_rate = 0.072 + rate_shift_bp / 10000.0
    invest_yield = 0.056 + rate_shift_bp / 20000.0
    # Notional: interest on net rather than gross.
    if meta["notional_interest"]:
        net_need = max(0.0, funding)
        int_exp = borrowing_cost(net_need, borrow_rate, 1.0)
        int_inc = interest_income(invested, invest_yield, 1.0)
    else:
        int_exp = borrowing_cost(funding, borrow_rate, 1.0)
        int_inc = interest_income(invested, invest_yield * 0.85, 1.0)

    # Baseline-like local borrowing if unpooled funding remains.
    avoided = 0.0
    if meta["physical"] or meta["notional_interest"]:
        avoided = borrowing_cost(max(0.0, sum(p.inr_funding for p in positions) - funding), borrow_rate, 1.0)

    benefit = pooling_benefit(avoided, extra_invested * invest_yield, pooling_cost)
    efficiency = liquidity_efficiency_score(
        cash_utilization=1 - (idle / cash if cash else 0),
        idle_cash_ratio=idle / cash if cash else 0,
        funding_dependency=funding / cash if cash else 0,
        investment_deployment=invested / cash if cash else 0,
        fx_exposure_ratio=fx / cash if cash else 0,
        wc_efficiency=0.62,
    )

    return {
        "strategy": strategy,
        "name": meta["name"],
        "positions": all_pos,
        "transfers": transfers,
        "totals": {
            "cash": cash,
            "idle": idle,
            "funding": funding,
            "invested": invested,
            "fx": fx,
            "inflows": inflows,
            "outflows": outflows,
            "interest_income": int_inc,
            "interest_expense": int_exp,
            "pooling_cost": pooling_cost,
            "pooling_benefit": benefit,
            "efficiency": efficiency,
            "complexity": meta["complexity"],
            "extra_invested": extra_invested,
        },
        "params": {
            "members": params.members,
            "min_buffer_mult": params.min_buffer_mult,
            "transfer_threshold": params.transfer_threshold,
            "investment_threshold": params.investment_threshold,
            "borrowing_threshold": params.borrowing_threshold,
        },
        "notes": _strategy_notes(strategy, transfers, funding, idle),
    }


def _strategy_notes(strategy: str, transfers: list, funding: float, idle: float) -> list[str]:
    notes = []
    if strategy == "none":
        notes.append("Each country stands alone. Surplus in India does not help a Singapore deficit.")
    if strategy == "physical":
        notes.append("Cash moves to the UK header, then to deficit entities. Cross-border FX and legal rails apply.")
    if strategy == "notional":
        notes.append("Balances stay put. Interest is calculated on the netted position, subject to the bank mandate.")
        notes.append("Idle cash is only marginally reduced because the cash is not physically redeployed.")
    if strategy == "hybrid":
        notes.append("Material deficits are funded with physical sweeps; residual balances notionally net for interest.")
    if transfers:
        total = sum(t["amount_inr"] for t in transfers)
        notes.append(f"Simulated sweeps total ₹{total:.1f} Cr. Singapore avoids external borrowing if the deficit is covered.")
    if funding > 0.5:
        notes.append(f"Residual group funding need remains ₹{funding:.1f} Cr after this structure.")
    notes.append("Real-world feasibility depends on jurisdiction, banking structure, tax rules, capital controls, and legal arrangements.")
    return notes


def compare_strategies(
    positions: list[Position],
    params: Optional[PoolParams] = None,
    rate_shift_bp: float = 0.0,
    weights: Optional[dict] = None,
) -> dict:
    weights = weights or {"liquidity": 0.4, "cost": 0.3, "fx": 0.2, "return": 0.1}
    results = {
        sid: simulate_strategy(positions, sid, params, rate_shift_bp) for sid in ("none", "physical", "notional", "hybrid")
    }
    baseline = results["none"]["totals"]
    scored = []
    for sid, res in results.items():
        t = res["totals"]
        idle_red = reduction_pct(baseline["idle"], t["idle"])
        cost_save = baseline["interest_expense"] - t["interest_expense"] + t["interest_income"] - baseline["interest_income"]
        fx_red = reduction_pct(baseline["fx"], t["fx"])
        liq = clamp(t["efficiency"])
        cost_s = clamp(50 + cost_save * 8)
        fx_s = clamp(70 + fx_red * 80)
        ret_s = clamp(t["interest_income"] * 6)
        overall = weighted_score(
            {"liquidity": liq, "cost": cost_s, "fx": fx_s, "return": ret_s},
            weights,
        )
        scored.append(
            {
                "id": sid,
                "name": res["name"],
                "idle": t["idle"],
                "funding": t["funding"],
                "financing_cost": t["interest_expense"],
                "investment_income": t["interest_income"],
                "fx": t["fx"],
                "efficiency": t["efficiency"],
                "complexity": t["complexity"],
                "benefit": t["pooling_benefit"],
                "idle_reduction": idle_red,
                "score": round(overall, 1),
                "components": {
                    "liquidity": round(liq, 1),
                    "cost": round(cost_s, 1),
                    "fx": round(fx_s, 1),
                    "return": round(ret_s, 1),
                },
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    winner = scored[0]
    hybrid = results["hybrid"]["totals"]
    return {
        "baseline_idle": baseline["idle"],
        "optimized_idle": hybrid["idle"],
        "cash_released": baseline["idle"] - hybrid["idle"],
        "idle_reduction": reduction_pct(baseline["idle"], hybrid["idle"]),
        "financing_cost_baseline": baseline["interest_expense"],
        "financing_cost_optimized": hybrid["interest_expense"],
        "financing_savings": baseline["interest_expense"] - hybrid["interest_expense"],
        "investment_income_baseline": baseline["interest_income"],
        "investment_income_optimized": hybrid["interest_income"],
        "fx_baseline": baseline["fx"],
        "fx_optimized": hybrid["fx"],
        "fx_reduction": reduction_pct(baseline["fx"], hybrid["fx"]),
        "winner": winner,
        "scorecard": scored,
        "results": results,
        "weights": weights,
        "label": "SIMULATED OPTIMIZATION RESULT",
    }


def serialize_position(p: Position, reporting: str, fx: dict[str, float]) -> dict:
    def c(v: float) -> float:
        return convert_inr_cr(v, reporting, fx)

    return {
        "country": p.country,
        "currency": p.currency,
        "personality": p.personality,
        "status": p.status,
        "closing": c(p.inr_closing),
        "min_cash": c(p.inr_min),
        "invested": c(p.inr_invested),
        "idle": c(p.inr_idle),
        "funding": c(p.inr_funding),
        "surplus": c(p.inr_surplus),
        "fx": c(p.inr_fx),
        "inflows": c(p.inr_inflows),
        "outflows": c(p.inr_outflows),
        "inr": {
            "closing": p.inr_closing,
            "idle": p.inr_idle,
            "funding": p.inr_funding,
            "fx": p.inr_fx,
        },
    }


def reporting_meta(reporting: str, fx: dict[str, float]) -> dict:
    return {
        "currency": reporting,
        "symbol": symbol_for(reporting),
        "unit": unit_for(reporting),
        "fx": fx,
        "disclaimer": "SIMULATED CORPORATE TREASURY DATA",
    }
