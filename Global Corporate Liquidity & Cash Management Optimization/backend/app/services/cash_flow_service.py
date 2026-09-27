from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.formulas import cash_runway, mean
from app.models.entities import CashFlow
from app.treasury.engine import PoolParams, positions_at, reporting_meta, scenario_params, serialize_position, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map, monthly_rows


def cash_flows(
    db: Session,
    country: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    reporting: str = "INR",
    scenario: str = "base",
    granularity: str = "month",
) -> dict:
    fx = latest_fx_map(db)
    sc = scenario_params(db, scenario)
    q = db.query(CashFlow).filter(CashFlow.granularity == granularity)
    if country and country not in ("ALL", "GLOBAL"):
        q = q.filter(CashFlow.country == country)
    if start:
        q = q.filter(CashFlow.period >= start)
    if end:
        q = q.filter(CashFlow.period <= end)
    rows = q.order_by(CashFlow.period, CashFlow.country).all()

    series = []
    for r in rows:
        inflows = r.inr_inflows * sc["collection_factor"] * (1 + sc["fx_inr_shock"])
        outflows = r.inr_outflows * sc["outflow_factor"] * (1 + sc["fx_inr_shock"])
        series.append(
            {
                "period": r.period.isoformat(),
                "country": r.country,
                "currency": r.currency,
                "business_unit": r.business_unit,
                "opening": convert_inr_cr(r.inr_closing - (r.inr_inflows - r.inr_outflows), reporting, fx),
                "inflows": convert_inr_cr(inflows, reporting, fx),
                "outflows": convert_inr_cr(outflows, reporting, fx),
                "closing": convert_inr_cr(r.inr_closing * (1 + sc["fx_inr_shock"]), reporting, fx),
                "customer_receipts": convert_inr_cr(r.customer_receipts / max(r.inflows, 1e-9) * inflows, reporting, fx)
                if r.currency == "INR"
                else convert_inr_cr(r.inr_inflows * 0.71 * sc["collection_factor"], reporting, fx),
                "supplier_payments": convert_inr_cr(r.inr_outflows * 0.38 * sc["outflow_factor"], reporting, fx),
                "payroll": convert_inr_cr(r.inr_outflows * 0.22 * sc["outflow_factor"], reporting, fx),
                "taxes": convert_inr_cr(r.inr_outflows * 0.08 * sc["outflow_factor"], reporting, fx),
                "capex": convert_inr_cr(r.inr_outflows * 0.08 * sc["outflow_factor"], reporting, fx),
                "debt_service": convert_inr_cr(r.inr_outflows * 0.075 * sc["outflow_factor"], reporting, fx),
                "other_inflows": convert_inr_cr(inflows * 0.29, reporting, fx),
                "idle": convert_inr_cr(r.inr_idle * (1 + sc["fx_inr_shock"]), reporting, fx),
                "funding": convert_inr_cr(r.inr_funding * (1 + sc["fx_inr_shock"]), reporting, fx),
                "min_cash": convert_inr_cr(r.inr_min_cash * (1 + sc["fx_inr_shock"]), reporting, fx),
                "fx": convert_inr_cr(r.inr_fx_exposure, reporting, fx),
            }
        )

    # Waterfall for latest month (or last in range)
    latest = [s for s in series if country in (None, "ALL", "GLOBAL", s["country"])]
    waterfall = []
    if latest:
        # Aggregate last period
        last_period = max(s["period"] for s in series)
        chunk = [s for s in series if s["period"] == last_period]
        if country not in (None, "ALL", "GLOBAL"):
            chunk = [s for s in chunk if s["country"] == country]
        agg = _sum_keys(chunk)
        opening = agg["closing"] - agg["inflows"] + agg["outflows"]
        waterfall = [
            {"key": "opening", "label": "Opening Cash", "value": opening, "type": "total"},
            {"key": "customer", "label": "Customer Receipts", "value": agg["customer_receipts"], "type": "in"},
            {"key": "other_in", "label": "Other Inflows", "value": agg["other_inflows"], "type": "in"},
            {"key": "supplier", "label": "Supplier Payments", "value": -agg["supplier_payments"], "type": "out"},
            {"key": "payroll", "label": "Payroll", "value": -agg["payroll"], "type": "out"},
            {"key": "taxes", "label": "Taxes", "value": -agg["taxes"], "type": "out"},
            {"key": "capex", "label": "Capex", "value": -agg["capex"], "type": "out"},
            {"key": "debt", "label": "Debt Service", "value": -agg["debt_service"], "type": "out"},
            {"key": "closing", "label": "Closing Cash", "value": agg["closing"], "type": "total"},
        ]

    return {
        "meta": reporting_meta(reporting, fx),
        "series": series,
        "waterfall": waterfall,
        "totals": _sum_keys(series) if series else {},
    }


def _sum_keys(rows: list[dict]) -> dict:
    keys = [
        "inflows",
        "outflows",
        "closing",
        "customer_receipts",
        "supplier_payments",
        "payroll",
        "taxes",
        "capex",
        "debt_service",
        "other_inflows",
        "idle",
        "funding",
        "min_cash",
        "fx",
    ]
    out = {k: 0.0 for k in keys}
    for r in rows:
        for k in keys:
            out[k] += r.get(k, 0.0)
    if rows:
        # closing is not a sum across months — if multiple countries same month, sum; if time series, take last month
        periods = {r["period"] for r in rows}
        if len(periods) > 1:
            last = max(r["period"] for r in rows)
            out["closing"] = sum(r["closing"] for r in rows if r["period"] == last)
            out["idle"] = sum(r.get("idle", 0) for r in rows if r["period"] == last)
            out["funding"] = sum(r.get("funding", 0) for r in rows if r["period"] == last)
            out["min_cash"] = sum(r.get("min_cash", 0) for r in rows if r["period"] == last)
    return out


def overview(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    strategy: str = "none",
    country: str = "ALL",
    params: Optional[PoolParams] = None,
) -> dict:
    fx = latest_fx_map(db)
    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, strategy, params)
    hist = monthly_rows(db, None, date(2025, 9, 30), AS_OF)
    by_month: dict[str, dict] = {}
    for r in hist:
        key = r.period.isoformat()
        by_month.setdefault(key, {"cash": 0, "inflows": 0, "outflows": 0, "idle": 0, "funding": 0, "fx": 0, "invested": 0, "financing": 0})
        by_month[key]["cash"] += r.inr_closing
        by_month[key]["inflows"] += r.inr_inflows
        by_month[key]["outflows"] += r.inr_outflows
        by_month[key]["idle"] += r.inr_idle
        by_month[key]["funding"] += r.inr_funding
        by_month[key]["fx"] += r.inr_fx_exposure
        by_month[key]["invested"] += r.inr_invested
        by_month[key]["financing"] += r.inr_funding * 0.072 / 12

    spark = []
    for k in sorted(by_month):
        row = {kk: convert_inr_cr(vv, reporting, fx) for kk, vv in by_month[k].items()}
        row["period"] = k
        spark.append(row)

    t = sim["totals"]
    prev = spark[-2] if len(spark) > 1 else spark[-1] if spark else {}

    def kpi(key, value, prev_val, definition):
        change = 0.0 if not prev_val else (value - prev_val) / abs(prev_val) if prev_val else 0
        return {
            "key": key,
            "value": value,
            "change": change,
            "spark": [s.get({"cash": "cash", "inflows": "inflows", "outflows": "outflows", "idle": "idle", "funding": "funding", "fx": "fx", "invested": "invested", "financing": "financing"}[key], 0) for s in spark],
            "definition": definition,
        }

    cfun = lambda v: convert_inr_cr(v, reporting, fx)
    kpis = [
        kpi("cash", cfun(t["cash"]), prev.get("cash"), "Group closing cash in reporting currency. Simulated."),
        kpi("inflows", cfun(t["inflows"]), prev.get("inflows"), "Monthly operating and non-operating receipts."),
        kpi("outflows", cfun(t["outflows"]), prev.get("outflows"), "Monthly operating, tax, capex and debt outflows."),
        kpi("idle", cfun(t["idle"]), prev.get("idle"), "Idle Cash = Closing − Required operating cash − Invested."),
        kpi("funding", cfun(t["funding"]), prev.get("funding"), "Funding gap where closing cash is below the minimum buffer."),
        kpi("fx", cfun(t["fx"]), prev.get("fx"), "Unhedged transactional FX exposure, INR-converted."),
        kpi("invested", cfun(t["invested"]), prev.get("invested"), "Short-term treasury investments. Illustrative allocation."),
        kpi("financing", cfun(t["interest_expense"]), prev.get("financing"), "Interest Expense = Borrowing × Rate × Time."),
    ]

    mapped = [serialize_position(p, reporting, fx) for p in sim["positions"]]
    if country not in ("ALL", "GLOBAL"):
        mapped = [p for p in mapped if p["country"] == country]

    daily_out = mean([r.inr_outflows / 30.4 for r in snapshot_rows_safe(db)])
    runway = cash_runway(t["cash"], daily_out if daily_out else 1)

    return {
        "meta": reporting_meta(reporting, fx),
        "as_of": AS_OF.isoformat(),
        "scenario": scenario,
        "strategy": strategy,
        "kpis": kpis,
        "map": mapped,
        "spark": spark,
        "transfers": sim["transfers"],
        "runway_days": runway,
        "status": _group_status(t),
        "annual_flow_inr": _annual_flow(db),
        "notes": sim["notes"],
    }


def snapshot_rows_safe(db):
    from app.utils.fx import snapshot_rows

    return snapshot_rows(db, AS_OF)


def _group_status(t: dict) -> dict:
    from app.analytics.formulas import traffic_light

    code = traffic_light(
        (t["cash"] - t["idle"] - t["funding"]) / t["cash"] if t["cash"] else 0,
        t["funding"],
        t["cash"] * 0.25 if t["cash"] else 1,
    )
    why = {
        "SAFE": "Group surplus covers the minimum cash buffer with headroom ≥ 15%.",
        "WATCH": "Headroom versus the minimum buffer is thin (< 15%).",
        "TIGHT": "At least one material funding gap exists versus minimum cash.",
        "FUNDING_REQUIRED": "Funding gap exceeds 15% of the reference buffer.",
    }
    return {"code": code, "why": why[code], "funding": t["funding"], "idle": t["idle"], "cash": t["cash"]}


def _annual_flow(db: Session) -> dict:
    rows = monthly_rows(db, None, date(2025, 1, 31), date(2025, 12, 31))
    inf = sum(r.inr_inflows for r in rows)
    out = sum(r.inr_outflows for r in rows)
    return {"year": 2025, "inflows": inf, "outflows": out, "gross": inf + out}
