from sqlalchemy.orm import Session

from app.analytics.formulas import liquidity_efficiency_score
from app.models.entities import Country, TreasuryEvent
from app.services.optimization_service import optimize
from app.treasury.engine import positions_at, reporting_meta, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


RULES = [
    {
        "id": "idle_invest",
        "if": "Idle cash > investment threshold",
        "then": "Consider deploying excess liquidity into approved short-term instruments.",
    },
    {
        "id": "pool_gap",
        "if": "Country A has surplus AND Country B has deficit",
        "then": "Pooling may reduce external borrowing requirements.",
    },
    {
        "id": "fx_review",
        "if": "FX exposure > threshold",
        "then": "Review hedging or natural-offset opportunities.",
    },
    {
        "id": "buffer",
        "if": "Liquidity buffer < minimum",
        "then": "Prioritize liquidity preservation over investment return.",
    },
]


def strategy_pack(db: Session, reporting: str = "INR", scenario: str = "base", weights: dict | None = None) -> dict:
    fx = latest_fx_map(db)
    opt = optimize(db, reporting, scenario, weights)
    pos = positions_at(db, AS_OF, scenario)
    none = simulate_strategy(pos, "none")
    hyb = simulate_strategy(pos, "hybrid")
    t = hyb["totals"]
    b = none["totals"]
    score = t["efficiency"]
    alerts = _alerts(pos, none, hyb)
    health = {
        "liquidity": _stars(score),
        "visibility": 4,
        "fx": 3 if t["fx"] > b["fx"] * 0.9 else 4,
        "funding": 5 if t["funding"] < b["funding"] * 0.5 else 4,
        "investment": 4 if t["invested"] > b["invested"] else 3,
    }
    findings = [
        "The company holds excess liquidity across multiple jurisdictions — India in particular.",
        "Cash pooling reduces fragmentation between surplus India and tight Singapore.",
        "Short-term investment of excess operating cash improves cash utilization.",
        "Working-capital improvements (DSO) can release additional cash without new capital.",
        "FX movements create material changes in reported INR liquidity.",
        "A hybrid strategy provides the best balance in the simulated model.",
    ]
    winner = opt["winner"]
    return {
        "meta": reporting_meta(reporting, fx),
        "recommended": {
            "id": winner["id"],
            "name": winner["name"],
            "reasons": [
                "reduces idle cash",
                "offsets local funding deficits",
                "improves group liquidity",
                "reduces unnecessary borrowing",
                "preserves minimum cash buffers",
                "improves short-term investment deployment",
            ],
            "idle_reduction": opt["idle_reduction"],
            "financing_savings": opt["financing_savings"],
            "fx_reduction": opt["fx_reduction"],
            "efficiency": score,
        },
        "what_could_go_wrong": [
            "Banking counterparties may not offer true notional pooling across these four jurisdictions.",
            "India surplus sweeps can create taxable intercompany events.",
            "Physical pooling increases USD/INR and GBP/INR conversion volume.",
            "Stress collections can erase the apparent 12% idle-cash improvement.",
            "Investment of operating cash reduces same-day optionality.",
        ],
        "findings": findings,
        "rules": RULES,
        "alerts": alerts,
        "health": health,
        "efficiency": {
            "score": score,
            "label": "Project-defined metric.",
            "components": {
                "utilization": 1 - (t["idle"] / t["cash"] if t["cash"] else 0),
                "idle": t["idle"] / t["cash"] if t["cash"] else 0,
                "funding": t["funding"] / t["cash"] if t["cash"] else 0,
                "investment": t["invested"] / t["cash"] if t["cash"] else 0,
                "fx": t["fx"] / t["cash"] if t["cash"] else 0,
            },
        },
        "optimization": opt,
        "disclaimer": "Project rules and simulated results. Not universal treasury policy.",
    }


def _stars(score: float) -> int:
    if score >= 88:
        return 5
    if score >= 75:
        return 4
    if score >= 62:
        return 3
    if score >= 50:
        return 2
    return 1


def _alerts(pos, none, hyb) -> list[dict]:
    alerts = []
    for p in none["positions"]:
        if p.inr_idle > 20:
            alerts.append({"level": "warn", "text": f"{p.country} idle cash above the ₹20 Cr attention threshold.", "id": f"idle-{p.country}"})
        if p.inr_funding > 1:
            alerts.append({"level": "warn", "text": f"{p.country} shows a liquidity deficit versus its minimum cash buffer.", "id": f"def-{p.country}"})
    if none["totals"]["fx"] > 25:
        alerts.append({"level": "warn", "text": "Group FX exposure is elevated versus the internal review threshold.", "id": "fx"})
    if hyb["totals"]["funding"] < none["totals"]["funding"]:
        alerts.append({"level": "ok", "text": "Hybrid pooling reduces the group borrowing requirement.", "id": "pool-ok"})
    return alerts


def countries(db: Session) -> list[dict]:
    rows = db.query(Country).all()
    return [
        {
            "code": r.code,
            "name": r.name,
            "currency": r.currency,
            "personality": r.personality,
            "region": r.region,
            "min_cash_local": r.min_cash_local,
            "dso": r.dso,
            "dpo": r.dpo,
            "inventory_days": r.inventory_days,
            "notes": r.notes,
            "headquarters": bool(r.headquarters),
        }
        for r in rows
    ]


def events(db: Session, month: str | None = None) -> list[dict]:
    q = db.query(TreasuryEvent)
    if month:
        q = q.filter(TreasuryEvent.event_date >= f"{month}-01", TreasuryEvent.event_date <= f"{month}-31")
    else:
        q = q.filter(TreasuryEvent.event_date >= "2026-09-01", TreasuryEvent.event_date <= "2026-09-30")
    return [
        {
            "date": e.event_date.isoformat(),
            "country": e.country,
            "category": e.category,
            "label": e.label,
            "amount_local": e.amount_local,
            "amount_inr": e.amount_inr,
            "currency": e.currency,
            "icon": e.icon,
        }
        for e in q.order_by(TreasuryEvent.event_date).all()
    ]


def methodology() -> dict:
    return {
        "title": "Methodology",
        "disclaimer": "SIMULATED CORPORATE TREASURY DATA",
        "company": "Orion Global Industries is a fictional multinational used for this portfolio project.",
        "period": "January 2024 → December 2026 monthly book, with a September 2026 daily slice.",
        "generation": "A seeded NumPy generator creates seasonal inflows/outflows, named shocks, and mean-reverting cash balances.",
        "fx": "USD/INR, GBP/INR and SGD/INR follow a mild drift plus sinusoidal noise. Crosses are derived.",
        "rates": "Investment yields and borrowing rates are illustrative, not market quotes.",
        "working_capital": "DSO/DPO/Inventory days are country-level assumptions converted through monthly revenue and COGS.",
        "pooling": "Physical pooling transfers surplus above a threshold to cover deficits. Notional nets interest only. Hybrid does both.",
        "optimization": "Weights default to Liquidity 40% / Cost 30% / FX 20% / Return 10%. The winning strategy is the highest weighted score.",
        "twelve_pct": "The idle-cash reduction is computed as (baseline idle − hybrid idle) / baseline idle. The book is calibrated so this lands near 12% in the base case.",
        "limitations": [
            "Simulated data — not a real company.",
            "Simplified tax treatment.",
            "Simplified FX assumptions; no forward curve.",
            "No bank-specific pooling constraints or notional pooling legal opinions.",
            "No real transaction costs beyond a flat bps assumption.",
            "Simplified investment yields.",
            "Simplified intercompany funding — no transfer-pricing engine.",
            "No legal or tax advice.",
            "No actual treasury execution.",
        ],
        "formulas": {
            "closing_cash": "Opening + Inflows − Outflows",
            "liquidity_gap": "Available + Expected Inflows − Expected Outflows − Minimum Cash",
            "idle_cash": "Closing − Required Operating Cash − Invested (floored at 0)",
            "working_capital": "Receivables + Inventory − Payables",
            "ccc": "DSO + Inventory Days − DPO",
            "fx": "Foreign amount × FX rate",
            "interest_income": "Invested × Yield × Time",
            "borrowing_cost": "Borrowed × Rate × Time",
            "pooling_benefit": "Avoided borrowing cost + Additional investment income − Pooling costs",
        },
    }


def research(payload: dict, db: Session) -> dict:
    country = payload.get("country", "ALL")
    metric = payload.get("metric", "idle")
    scenario = payload.get("scenario", "base")
    strategy = payload.get("strategy", "hybrid")
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy)
    fx = latest_fx_map(db)
    reporting = payload.get("currency", "INR")
    mapped = {p.country: p for p in sim["positions"]}
    focus = list(mapped.values()) if country in ("ALL", "GLOBAL") else [mapped[country]]
    value = sum(getattr(p, {"idle": "inr_idle", "cash": "inr_closing", "funding": "inr_funding", "fx": "inr_fx"}.get(metric, "inr_idle")) for p in focus)
    return {
        "question": payload.get("question") or f"What is {metric} for {country} under {scenario} / {strategy}?",
        "data": f"Simulated Orion book, as-of {AS_OF.isoformat()}, reporting {reporting}.",
        "method": "Scenario overlay on the monthly cash book, then strategy simulation (pooling + investment deployment).",
        "result": convert_inr_cr(value, reporting, fx),
        "interpretation": "Read the result next to the minimum cash buffer and the idle-cash definition. Direction matters more than the precise decimal.",
        "limitations": "Simulated. No bank constraints. Simplified FX and tax.",
        "meta": reporting_meta(reporting, fx),
    }
