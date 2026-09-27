from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.entities import CashFlow
from app.treasury.engine import positions_at, reporting_meta, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map, monthly_rows


def matrix(db: Session, reporting: str = "INR", scenario: str = "base", strategy: str = "none") -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy)
    rows = ["inflows", "outflows", "closing", "min_cash", "idle", "funding", "fx", "invested"]
    attr = {
        "inflows": "inr_inflows",
        "outflows": "inr_outflows",
        "closing": "inr_closing",
        "min_cash": "inr_min",
        "idle": "inr_idle",
        "funding": "inr_funding",
        "fx": "inr_fx",
        "invested": "inr_invested",
    }
    columns = [p.country for p in sim["positions"]]
    data = []
    for row in rows:
        line = {"metric": row}
        for p in sim["positions"]:
            line[p.country] = convert_inr_cr(getattr(p, attr[row]), reporting, fx)
        data.append(line)
    return {"meta": reporting_meta(reporting, fx), "columns": columns, "rows": data}


def concentration(db: Session, reporting: str = "INR") -> dict:
    fx = latest_fx_map(db)
    rows = monthly_rows(db, None, date(2025, 1, 31), date(2025, 12, 31))
    cash = {}
    rev = {}
    for r in rows:
        cash[r.country] = cash.get(r.country, 0) + r.inr_closing
        rev[r.country] = rev.get(r.country, 0) + r.inr_inflows
    # Average cash over the year
    n = 12
    cash = {k: v / n for k, v in cash.items()}
    tot_c = sum(cash.values()) or 1
    tot_r = sum(rev.values()) or 1
    return {
        "meta": reporting_meta(reporting, fx),
        "series": [
            {
                "country": k,
                "cash_share": cash[k] / tot_c,
                "revenue_share": rev[k] / tot_r,
                "cash": convert_inr_cr(cash[k], reporting, fx),
                "revenue": convert_inr_cr(rev[k], reporting, fx),
            }
            for k in cash
        ],
        "risk": "If cash concentration diverges from revenue concentration, a single jurisdiction shock can strand liquidity.",
    }


def country_dashboard(db: Session, code: str, reporting: str = "INR", scenario: str = "base", strategy: str = "none") -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy)
    p = next(x for x in sim["positions"] if x.country == code)
    hist = monthly_rows(db, code, date(2025, 1, 31), AS_OF)
    trend = [
        {
            "period": r.period.isoformat()[:7],
            "cash": convert_inr_cr(r.inr_closing, reporting, fx),
            "inflows": convert_inr_cr(r.inr_inflows, reporting, fx),
            "outflows": convert_inr_cr(r.inr_outflows, reporting, fx),
            "idle": convert_inr_cr(r.inr_idle, reporting, fx),
            "wc": convert_inr_cr(r.working_capital * (r.inr_closing / r.closing_cash if r.closing_cash else 1), reporting, fx),
            "fx": convert_inr_cr(r.inr_fx_exposure, reporting, fx),
            "invested": convert_inr_cr(r.inr_invested, reporting, fx),
            "funding": convert_inr_cr(r.inr_funding, reporting, fx),
        }
        for r in hist
    ]
    return {
        "meta": reporting_meta(reporting, fx),
        "country": code,
        "personality": p.personality,
        "kpis": {
            "cash": convert_inr_cr(p.inr_closing, reporting, fx),
            "inflows": convert_inr_cr(p.inr_inflows, reporting, fx),
            "outflows": convert_inr_cr(p.inr_outflows, reporting, fx),
            "idle": convert_inr_cr(p.inr_idle, reporting, fx),
            "wc": trend[-1]["wc"] if trend else 0,
            "fx": convert_inr_cr(p.inr_fx, reporting, fx),
            "funding": convert_inr_cr(p.inr_funding, reporting, fx),
            "min_cash": convert_inr_cr(p.inr_min, reporting, fx),
            "surplus": convert_inr_cr(p.inr_surplus, reporting, fx),
            "invested": convert_inr_cr(p.inr_invested, reporting, fx),
        },
        "trend": trend,
        "status": p.status,
    }


def sankey(db: Session, reporting: str = "INR", strategy: str = "hybrid") -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, "base")
    sim = simulate_strategy(pos, strategy)
    nodes = [
        {"id": "customers", "label": "Customers"},
        {"id": "IN", "label": "India"},
        {"id": "US", "label": "United States"},
        {"id": "UK", "label": "United Kingdom"},
        {"id": "SG", "label": "Singapore"},
        {"id": "opex", "label": "Operating expenses"},
        {"id": "pool", "label": "Cash pool"},
        {"id": "invest", "label": "Investments"},
        {"id": "borrow", "label": "Borrowing"},
    ]
    links = []
    for p in sim["positions"]:
        links.append({"source": "customers", "target": p.country, "value": convert_inr_cr(p.inr_inflows, reporting, fx)})
        links.append({"source": p.country, "target": "opex", "value": convert_inr_cr(p.inr_outflows * 0.72, reporting, fx)})
        if p.inr_invested > 0.2:
            links.append({"source": p.country, "target": "invest", "value": convert_inr_cr(p.inr_invested, reporting, fx)})
        if p.inr_funding > 0.2:
            links.append({"source": "borrow", "target": p.country, "value": convert_inr_cr(p.inr_funding, reporting, fx)})
    for t in sim["transfers"]:
        links.append({"source": t["from"], "target": "pool", "value": convert_inr_cr(t["amount_inr"], reporting, fx)})
        links.append({"source": "pool", "target": t["to"], "value": convert_inr_cr(t["amount_inr"], reporting, fx)})
    return {"meta": reporting_meta(reporting, fx), "nodes": nodes, "links": links}
