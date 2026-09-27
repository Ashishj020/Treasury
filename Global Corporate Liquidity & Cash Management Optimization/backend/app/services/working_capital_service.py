from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.formulas import cash_conversion_cycle, cash_released_from_days, dpo, dso, working_capital
from app.models.entities import Payable, Receivable, WorkingCapitalRow
from app.treasury.engine import reporting_meta
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


def working_capital_pack(
    db: Session,
    reporting: str = "INR",
    country: Optional[str] = None,
    dso_adj: Optional[float] = None,
    dpo_adj: Optional[float] = None,
    inv_adj: Optional[float] = None,
) -> dict:
    fx = latest_fx_map(db)
    q = db.query(WorkingCapitalRow).filter(WorkingCapitalRow.period == AS_OF)
    if country and country not in ("ALL", "GLOBAL"):
        q = q.filter(WorkingCapitalRow.country == country)
    rows = q.all()
    revenue = sum(r.inr_revenue for r in rows) * 12
    cogs = sum(r.inr_cogs for r in rows) * 12
    ar = sum(r.ar / r.revenue * r.inr_revenue if r.revenue else 0 for r in rows)
    # Use INR WC components
    ar_inr = sum(r.inr_wc * (r.ar / r.wc) if r.wc else 0 for r in rows)
    ap_inr = sum((r.ap / r.wc) * r.inr_wc if r.wc else 0 for r in rows)
    inv_inr = sum((r.inventory / r.wc) * r.inr_wc if r.wc else 0 for r in rows)
    # Safer: scale local ratios via inr_revenue
    ar_inr = sum(r.inr_revenue * (r.dso / 30.4) for r in rows)
    ap_inr = sum(r.inr_cogs * (r.dpo / 30.4) for r in rows)
    inv_inr = sum(r.inr_cogs * (r.inventory_days / 30.4) for r in rows)

    base_dso = dso(ar_inr, revenue) if revenue else 45
    base_dpo = dpo(ap_inr, cogs) if cogs else 36
    base_inv = (inv_inr / cogs * 365) if cogs else 40
    new_dso = dso_adj if dso_adj is not None else base_dso
    new_dpo = dpo_adj if dpo_adj is not None else base_dpo
    new_inv = inv_adj if inv_adj is not None else base_inv

    released_dso = cash_released_from_days(base_dso - new_dso, revenue)
    released_dpo = cash_released_from_days(new_dpo - base_dpo, cogs)
    released_inv = cash_released_from_days(base_inv - new_inv, cogs)
    released = released_dso + released_dpo + released_inv
    ccc0 = cash_conversion_cycle(base_dso, base_inv, base_dpo)
    ccc1 = cash_conversion_cycle(new_dso, new_inv, new_dpo)
    wc0 = working_capital(ar_inr, inv_inr, ap_inr)

    trend_q = db.query(WorkingCapitalRow)
    if country and country not in ("ALL", "GLOBAL"):
        trend_q = trend_q.filter(WorkingCapitalRow.country == country)
    trend_q = trend_q.filter(WorkingCapitalRow.period >= date(2025, 1, 31))
    trend_map: dict[str, dict] = {}
    for r in trend_q.all():
        k = r.period.isoformat()[:7]
        trend_map.setdefault(k, {"ccc": [], "wc": 0.0, "dso": [], "dpo": [], "inv": []})
        trend_map[k]["ccc"].append(r.ccc)
        trend_map[k]["wc"] += r.inr_wc
        trend_map[k]["dso"].append(r.dso)
        trend_map[k]["dpo"].append(r.dpo)
        trend_map[k]["inv"].append(r.inventory_days)
    trend = []
    for k in sorted(trend_map):
        t = trend_map[k]
        n = max(len(t["ccc"]), 1)
        trend.append(
            {
                "period": k,
                "ccc": sum(t["ccc"]) / n,
                "dso": sum(t["dso"]) / n,
                "dpo": sum(t["dpo"]) / n,
                "inventory_days": sum(t["inv"]) / n,
                "wc": convert_inr_cr(t["wc"], reporting, fx),
            }
        )

    return {
        "meta": reporting_meta(reporting, fx),
        "base": {
            "dso": base_dso,
            "dpo": base_dpo,
            "inventory_days": base_inv,
            "ccc": ccc0,
            "wc": convert_inr_cr(wc0, reporting, fx),
            "revenue": convert_inr_cr(revenue, reporting, fx),
            "cogs": convert_inr_cr(cogs, reporting, fx),
        },
        "adjusted": {
            "dso": new_dso,
            "dpo": new_dpo,
            "inventory_days": new_inv,
            "ccc": ccc1,
        },
        "released": {
            "dso": convert_inr_cr(released_dso, reporting, fx),
            "dpo": convert_inr_cr(released_dpo, reporting, fx),
            "inventory": convert_inr_cr(released_inv, reporting, fx),
            "total": convert_inr_cr(released, reporting, fx),
        },
        "bridge": [
            {"label": "Starting WC cash tied", "value": convert_inr_cr(wc0, reporting, fx)},
            {"label": "DSO change", "value": convert_inr_cr(-released_dso, reporting, fx)},
            {"label": "DPO change", "value": convert_inr_cr(-released_dpo, reporting, fx)},
            {"label": "Inventory days change", "value": convert_inr_cr(-released_inv, reporting, fx)},
            {"label": "Ending WC cash tied", "value": convert_inr_cr(wc0 - released, reporting, fx)},
        ],
        "trend": trend,
        "formulas": {
            "dso": "Average AR / Revenue × 365",
            "dpo": "Average AP / COGS × 365",
            "inventory_days": "Average Inventory / COGS × 365",
            "ccc": "DSO + Inventory Days − DPO",
            "release": "Annual flow × Δdays / 365",
        },
        "explain": {
            "dso": "Days Sales Outstanding — how long cash is trapped in receivables.",
            "dpo": "Days Payable Outstanding — how long the company takes to pay suppliers (within terms).",
            "ccc": "Cash Conversion Cycle — days of cash tied in the operating cycle.",
            "release": "Reducing DSO by 5 days → faster collections → lower WC → more available cash.",
        },
    }


def receivables(db: Session, reporting: str = "INR", country: Optional[str] = None) -> dict:
    fx = latest_fx_map(db)
    q = db.query(Receivable).filter(Receivable.period == AS_OF)
    if country and country not in ("ALL", "GLOBAL"):
        q = q.filter(Receivable.country == country)
    rows = q.all()
    buckets = {}
    countries = {}
    overdue = 0.0
    total = 0.0
    for r in rows:
        buckets[r.bucket] = buckets.get(r.bucket, 0.0) + r.amount_inr
        countries.setdefault(r.country, 0.0)
        countries[r.country] += r.amount_inr
        total += r.amount_inr
        if r.overdue:
            overdue += r.amount_inr
    return {
        "meta": reporting_meta(reporting, fx),
        "buckets": [{"bucket": k, "amount": convert_inr_cr(v, reporting, fx)} for k, v in buckets.items()],
        "by_country": [{"country": k, "amount": convert_inr_cr(v, reporting, fx)} for k, v in countries.items()],
        "overdue": convert_inr_cr(overdue, reporting, fx),
        "total": convert_inr_cr(total, reporting, fx),
        "why": "Receivables are sales that have not yet become cash. Stretching DSO is a silent liquidity drain.",
    }


def payables(db: Session, reporting: str = "INR", country: Optional[str] = None, timing: str = "terms") -> dict:
    fx = latest_fx_map(db)
    q = db.query(Payable).filter(Payable.period == AS_OF)
    if country and country not in ("ALL", "GLOBAL"):
        q = q.filter(Payable.country == country)
    rows = q.all()
    by_status = {}
    total = 0.0
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0.0) + r.amount_inr
        total += r.amount_inr
    # Timing scenario — never models paying later than contractual terms.
    impact = 0.0
    note = "Pay on contractual terms. Liquidity is the scheduled outflow path."
    if timing == "immediate":
        impact = -total * 0.12
        note = "Paying immediately pulls cash forward. Liquidity tightens; supplier goodwill may improve."
    elif timing == "optimize":
        impact = total * 0.045
        note = "Paying on contractual due dates (not early) keeps cash longer without breaking terms."
    return {
        "meta": reporting_meta(reporting, fx),
        "status": [{"status": k, "amount": convert_inr_cr(v, reporting, fx)} for k, v in by_status.items()],
        "total": convert_inr_cr(total, reporting, fx),
        "timing": timing,
        "liquidity_impact": convert_inr_cr(impact, reporting, fx),
        "note": note,
        "disclaimer": "Do not treat delayed payment beyond contract as a treasury strategy.",
    }
