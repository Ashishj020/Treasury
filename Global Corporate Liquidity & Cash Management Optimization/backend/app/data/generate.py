"""Simulated multi-currency cash book for Orion Global Industries.

All figures are project-model data. Nothing here is a real company result.
"""

from __future__ import annotations

from datetime import date, timedelta
from math import sin

import numpy as np
from sqlalchemy.orm import Session

from app.analytics.formulas import (
    cash_conversion_cycle,
    closing_cash,
    dpo,
    dso,
    excess_cash,
    idle_cash,
    inventory_days,
    traffic_light,
    working_capital,
)
from app.database import Base, engine
from app.models.entities import (
    AnalysisResult,
    BorrowingFacility,
    CashFlow,
    Country,
    Currency,
    ExchangeRate,
    InvestmentOption,
    LiquidityPosition,
    Payable,
    PoolingStrategy,
    Receivable,
    ScenarioDef,
    TreasuryEvent,
    WorkingCapitalRow,
)


COUNTRY_PROFILES = {
    "IN": {
        "name": "India",
        "currency": "INR",
        "region": "South Asia",
        "personality": "Cash Rich",
        "flag": "IN",
        "hq": 0,
        "unit": "cr",
        "opening": 108.0,
        "min_cash": 60.0,
        "base_inflow": 36.4,
        "outflow_ratio": 0.905,
        "invested_share": 0.14,
        "fx_share": 0.18,
        "dso": 48.0,
        "dpo": 39.0,
        "inv_days": 46.0,
        "season": [0.90, 0.88, 1.04, 0.98, 1.02, 0.94, 0.96, 1.01, 1.10, 1.16, 1.22, 1.14],
        "bu": "Industrial & Consumer",
        "notes": "Largest surplus pool. Seasonal collections around festival demand.",
    },
    "US": {
        "name": "United States",
        "currency": "USD",
        "region": "North America",
        "personality": "Always Moving",
        "flag": "US",
        "hq": 0,
        "unit": "mn",
        "opening": 11.8,
        "min_cash": 5.4,
        "base_inflow": 12.6,
        "outflow_ratio": 0.97,
        "invested_share": 0.18,
        "fx_share": 0.22,
        "dso": 41.0,
        "dpo": 34.0,
        "inv_days": 38.0,
        "season": [0.92, 0.94, 1.00, 1.02, 1.04, 1.06, 1.02, 1.00, 1.05, 1.08, 1.18, 1.22],
        "bu": "Technology & Aftermarket",
        "notes": "High-velocity operating cash. Working-capital swings dominate liquidity.",
    },
    "UK": {
        "name": "United Kingdom",
        "currency": "GBP",
        "region": "Europe",
        "personality": "Buffer Builder",
        "flag": "GB",
        "hq": 1,
        "unit": "mn",
        "opening": 9.4,
        "min_cash": 6.8,
        "base_inflow": 6.1,
        "outflow_ratio": 0.94,
        "invested_share": 0.09,
        "fx_share": 0.28,
        "dso": 44.0,
        "dpo": 42.0,
        "inv_days": 33.0,
        "season": [0.86, 0.90, 1.02, 1.00, 1.03, 1.04, 0.98, 0.92, 1.06, 1.08, 1.10, 0.96],
        "bu": "Group & Europe",
        "notes": "Headquarters. Conservative minimum cash. Natural pooling header candidate.",
    },
    "SG": {
        "name": "Singapore",
        "currency": "SGD",
        "region": "Southeast Asia",
        "personality": "Efficient but Tight",
        "flag": "SG",
        "hq": 0,
        "unit": "mn",
        "opening": 6.6,
        "min_cash": 6.4,
        "base_inflow": 7.4,
        "outflow_ratio": 1.015,
        "invested_share": 0.02,
        "fx_share": 0.35,
        "dso": 51.0,
        "dpo": 28.0,
        "inv_days": 29.0,
        "season": [0.84, 0.90, 1.04, 0.98, 1.02, 0.88, 0.94, 1.00, 1.06, 1.10, 1.08, 1.12],
        "bu": "Regional Hub",
        "notes": "Trading hub with thin buffers. Periodic funding pressure versus India surplus.",
    },
}

BASE_FX = {
    "USDINR": 83.40,
    "GBPINR": 106.20,
    "SGDINR": 62.10,
    "USDGBP": 83.40 / 106.20,
    "USDSGD": 83.40 / 62.10,
}

INVESTMENTS = [
    ("overnight", "Overnight deposit", 1, 0.041, 98, "Same-day liquidity. Lowest yield."),
    ("mmf", "Money market fund", 7, 0.052, 90, "T+1 liquidity. Illustrative treasury allocation."),
    ("tbill", "Treasury bill", 91, 0.061, 75, "Hold-to-maturity unless repo'd."),
    ("cp", "Commercial paper", 60, 0.068, 62, "Credit-sensitive. Not a recommendation."),
    ("govt", "Short-duration government securities", 180, 0.066, 70, "Duration and mark-to-market risk."),
]

FACILITIES = [
    ("rcf_in", "India revolving credit", "INR", 0.092, 365, 40.0, 6.5, "IN"),
    ("rcf_us", "US revolving credit", "USD", 0.065, 365, 25.0, 3.2, "US"),
    ("stl_uk", "UK short-term loan", "GBP", 0.058, 180, 12.0, 1.1, "UK"),
    ("cp_us", "US commercial paper", "USD", 0.054, 45, 18.0, 2.4, "US"),
    ("ic_in_sg", "Intercompany IN→SG", "INR", 0.071, 90, 25.0, 0.0, "IN"),
]


def month_ends(start: date, end: date) -> list[date]:
    out: list[date] = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        if m == 12:
            last = date(y, 12, 31)
            y, m = y + 1, 1
        else:
            nxt = date(y, m + 1, 1)
            last = nxt - timedelta(days=1)
            m += 1
        out.append(last)
    return out


def inr_per_unit(currency: str, fx: dict[str, float]) -> float:
    if currency == "INR":
        return 1.0
    if currency == "USD":
        return fx["USDINR"]
    if currency == "GBP":
        return fx["GBPINR"]
    if currency == "SGD":
        return fx["SGDINR"]
    return 1.0


def to_inr_cr(amount_local: float, currency: str, fx: dict[str, float]) -> float:
    """Convert local units to INR crore.

    India is already stored in INR crore.
    USD/GBP/SGD are stored in millions of local currency.
    1 million foreign × FX / 10 = INR crore.
    """
    if currency == "INR":
        return amount_local
    return amount_local * inr_per_unit(currency, fx) / 10.0


def fx_for_month(i: int, rng: np.random.Generator) -> dict[str, float]:
    t = i / 12.0
    usd = BASE_FX["USDINR"] + 1.35 * t + 0.55 * sin(i / 3.2) + float(rng.normal(0, 0.18))
    gbp = BASE_FX["GBPINR"] + 0.40 * t + 0.70 * sin(i / 4.1 + 0.4) + float(rng.normal(0, 0.22))
    sgd = BASE_FX["SGDINR"] + 0.55 * t + 0.28 * sin(i / 2.7) + float(rng.normal(0, 0.10))
    return {
        "USDINR": round(usd, 4),
        "GBPINR": round(gbp, 4),
        "SGDINR": round(sgd, 4),
        "USDGBP": round(usd / gbp, 6),
        "USDSGD": round(usd / sgd, 6),
    }


def seed(db: Session, seed_value: int = 42) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rng = np.random.default_rng(seed_value)

    for code, p in COUNTRY_PROFILES.items():
        db.add(
            Country(
                code=code,
                name=p["name"],
                currency=p["currency"],
                region=p["region"],
                personality=p["personality"],
                flag=p["flag"],
                headquarters=p["hq"],
                min_cash_local=p["min_cash"],
                dso=p["dso"],
                dpo=p["dpo"],
                inventory_days=p["inv_days"],
                notes=p["notes"],
            )
        )

    db.add_all(
        [
            Currency(code="INR", name="Indian Rupee", symbol="₹", inr_per_unit_base=1.0),
            Currency(code="USD", name="US Dollar", symbol="$", inr_per_unit_base=BASE_FX["USDINR"]),
            Currency(code="GBP", name="Pound Sterling", symbol="£", inr_per_unit_base=BASE_FX["GBPINR"]),
            Currency(code="SGD", name="Singapore Dollar", symbol="S$", inr_per_unit_base=BASE_FX["SGDINR"]),
        ]
    )

    for item in INVESTMENTS:
        db.add(
            InvestmentOption(
                id=item[0],
                name=item[1],
                horizon_days=item[2],
                yield_pct=item[3],
                liquidity_score=item[4],
                risk_note=item[5],
            )
        )

    for item in FACILITIES:
        db.add(
            BorrowingFacility(
                id=item[0],
                name=item[1],
                currency=item[2],
                rate_pct=item[3],
                tenor_days=item[4],
                limit_local=item[5],
                drawn_local=item[6],
                country=item[7],
                notes="Illustrative facility. Not a live credit line.",
            )
        )

    db.add_all(
        [
            PoolingStrategy(
                id="none",
                name="No pooling",
                summary="Each country funds itself. Surplus sits idle locally; deficits are borrowed locally.",
                complexity=1,
                fx_friction=0.0,
                transfer_cost_bps=0.0,
            ),
            PoolingStrategy(
                id="physical",
                name="Physical cash pooling",
                summary="Surplus is physically swept to a header account (UK) and on-lent to deficit entities.",
                complexity=4,
                fx_friction=0.35,
                transfer_cost_bps=6.0,
            ),
            PoolingStrategy(
                id="notional",
                name="Notional pooling",
                summary="Balances stay in-country. The bank notions a net position for interest. Legal/tax feasibility varies.",
                complexity=3,
                fx_friction=0.08,
                transfer_cost_bps=1.5,
            ),
            PoolingStrategy(
                id="hybrid",
                name="Hybrid pooling",
                summary="Physical sweeps for material imbalances; notional interest netting for residual balances.",
                complexity=3,
                fx_friction=0.18,
                transfer_cost_bps=3.5,
            ),
        ]
    )

    db.add_all(
        [
            ScenarioDef(
                id="base",
                name="Base case",
                description="Normal collections, normal payments, moderate rates, stable FX.",
                collection_factor=1.0,
                outflow_factor=1.0,
                rate_shift_bp=0.0,
                fx_inr_shock=0.0,
                receivable_delay_days=0,
            ),
            ScenarioDef(
                id="optimistic",
                name="Optimistic",
                description="Faster collections, lighter outflows, modestly supportive FX.",
                collection_factor=1.06,
                outflow_factor=0.96,
                rate_shift_bp=-25.0,
                fx_inr_shock=-0.02,
                receivable_delay_days=-4,
            ),
            ScenarioDef(
                id="stressed",
                name="Stressed",
                description="Receivables delayed 15 days, opex +10%, rates +150bp, INR −8%.",
                collection_factor=0.88,
                outflow_factor=1.10,
                rate_shift_bp=150.0,
                fx_inr_shock=0.08,
                receivable_delay_days=15,
            ),
        ]
    )

    periods = month_ends(date(2024, 1, 1), date(2026, 12, 31))
    books: dict[str, float] = {c: COUNTRY_PROFILES[c]["opening"] for c in COUNTRY_PROFILES}
    annual_inflow_inr = 0.0
    annual_outflow_inr = 0.0

    for i, period in enumerate(periods):
        fx = fx_for_month(i, rng)
        for pair, rate in fx.items():
            db.add(ExchangeRate(as_of=period, pair=pair, rate=rate))

        month_idx = period.month - 1
        year = period.year

        for code, p in COUNTRY_PROFILES.items():
            season = p["season"][month_idx]
            noise = float(rng.normal(1.0, 0.035))
            shock = 1.0
            # Named cash shocks — not every month is smooth.
            if code == "IN" and period.month == 3:
                shock *= 0.91  # advance tax
            if code == "IN" and period.month in (10, 11):
                shock *= 1.08  # festival collections
            if code == "US" and period.month == 12:
                shock *= 1.07
            if code == "UK" and period.month == 1:
                shock *= 0.90
            if code == "SG" and period.month in (1, 6):
                shock *= 0.86  # funding-pressure months
            if code == "SG" and period == date(2025, 9, 30):
                shock *= 0.82  # one-off delayed receipt
            if code == "US" and period == date(2026, 3, 31):
                shock *= 1.12  # large customer receipt

            inflow = p["base_inflow"] * season * noise * shock
            customer = inflow * 0.71
            ar_coll = inflow * 0.14
            ic_in = inflow * 0.05
            int_inc = max(0.02, books[code] * 0.0035)
            asset = inflow * (0.04 if (code == "UK" and period.month == 7 and year == 2025) else 0.01)
            other_in = inflow - customer - ar_coll - ic_in - asset
            inflows = customer + ar_coll + ic_in + int_inc + asset + other_in

            raw_out = inflows * p["outflow_ratio"] * float(rng.normal(1.0, 0.028))
            if code == "IN" and period.month in (3, 9):
                raw_out *= 1.08
            if code == "SG" and period.month in (1, 6):
                raw_out *= 1.11
            if code == "US" and period.month == 4:
                raw_out *= 1.06  # tax
            if period.month == 8 and year == 2026 and code == "UK":
                raw_out *= 1.14  # capex spike

            supplier = raw_out * 0.38
            payroll = raw_out * 0.22
            taxes = raw_out * (0.11 if period.month in (3, 4, 9) else 0.06)
            rent = raw_out * 0.04
            capex = raw_out * (0.14 if period.month in (2, 8) else 0.06)
            debt_rep = raw_out * 0.05
            int_exp = raw_out * 0.025
            ic_out = raw_out * 0.03
            opex = max(0.1, raw_out - (supplier + payroll + taxes + rent + capex + debt_rep + int_exp + ic_out))
            outflows = supplier + payroll + taxes + rent + capex + debt_rep + int_exp + ic_out + opex

            opening = books[code]
            closing = closing_cash(opening, inflows, outflows)
            # Gentle mean-reversion toward a target cash level so 2026 remains realistic.
            target = p["opening"] * (1.08 if code == "IN" else 0.96 if code == "SG" else 1.02)
            closing = 0.82 * closing + 0.18 * target
            books[code] = closing

            min_cash = p["min_cash"] * (1.0 + 0.015 * sin(i / 5))
            surplus = excess_cash(closing, min_cash)
            funding = max(0.0, -surplus)
            invested = max(0.0, min(closing * p["invested_share"], max(0.0, surplus * 0.45)))
            idle = idle_cash(closing, min_cash, invested)
            fx_exp = abs(inflows - outflows) * p["fx_share"]
            debt_svc = debt_rep + int_exp

            revenue = customer + ar_coll
            cogs = supplier * 1.05
            ar = revenue * p["dso"] / 30.4
            ap = cogs * p["dpo"] / 30.4
            inv = cogs * p["inv_days"] / 30.4
            wc = working_capital(ar, inv, ap)
            dso_v = dso(ar, revenue * 12)
            dpo_v = dpo(ap, cogs * 12)
            inv_d = inventory_days(inv, cogs * 12)
            ccc_v = cash_conversion_cycle(dso_v, inv_d, dpo_v)

            inr_in = to_inr_cr(inflows, p["currency"], fx)
            inr_out = to_inr_cr(outflows, p["currency"], fx)
            inr_close = to_inr_cr(closing, p["currency"], fx)
            inr_idle = to_inr_cr(idle, p["currency"], fx)
            inr_fund = to_inr_cr(funding, p["currency"], fx)
            inr_fx = to_inr_cr(fx_exp, p["currency"], fx)
            inr_inv = to_inr_cr(invested, p["currency"], fx)
            inr_min = to_inr_cr(min_cash, p["currency"], fx)

            if year == 2025:
                annual_inflow_inr += inr_in
                annual_outflow_inr += inr_out

            db.add(
                CashFlow(
                    country=code,
                    period=period,
                    granularity="month",
                    currency=p["currency"],
                    opening_cash=opening,
                    customer_receipts=customer,
                    ar_collections=ar_coll,
                    intercompany_receipts=ic_in,
                    interest_income=int_inc,
                    asset_sales=asset,
                    other_inflows=other_in,
                    supplier_payments=supplier,
                    payroll=payroll,
                    taxes=taxes,
                    rent=rent,
                    capex=capex,
                    debt_repayment=debt_rep,
                    interest_expense=int_exp,
                    intercompany_transfers=ic_out,
                    opex=opex,
                    inflows=inflows,
                    outflows=outflows,
                    closing_cash=closing,
                    receivables=ar,
                    payables=ap,
                    inventory=inv,
                    payroll_accrual=payroll * 0.35,
                    taxes_accrual=taxes * 0.4,
                    working_capital=wc,
                    min_cash=min_cash,
                    surplus_cash=max(0.0, surplus),
                    funding_gap=funding,
                    invested_cash=invested,
                    idle_cash=idle,
                    fx_exposure=fx_exp,
                    debt_service=debt_svc,
                    inr_inflows=inr_in,
                    inr_outflows=inr_out,
                    inr_closing=inr_close,
                    inr_idle=inr_idle,
                    inr_funding=inr_fund,
                    inr_fx_exposure=inr_fx,
                    inr_invested=inr_inv,
                    inr_min_cash=inr_min,
                    business_unit=p["bu"],
                )
            )

            status = traffic_light(
                surplus / min_cash if min_cash else 0.0,
                funding,
                min_cash,
            )
            db.add(
                LiquidityPosition(
                    country=code,
                    period=period,
                    opening=opening,
                    closing=closing,
                    min_cash=min_cash,
                    surplus=max(0.0, surplus),
                    funding=funding,
                    idle=idle,
                    invested=invested,
                    status=status,
                    inr_closing=inr_close,
                    inr_idle=inr_idle,
                    inr_funding=inr_fund,
                    inr_surplus=to_inr_cr(max(0.0, surplus), p["currency"], fx),
                )
            )

            db.add(
                WorkingCapitalRow(
                    country=code,
                    period=period,
                    revenue=revenue,
                    cogs=cogs,
                    ar=ar,
                    ap=ap,
                    inventory=inv,
                    dso=dso_v,
                    dpo=dpo_v,
                    inventory_days=inv_d,
                    ccc=ccc_v,
                    wc=wc,
                    inr_revenue=to_inr_cr(revenue, p["currency"], fx),
                    inr_cogs=to_inr_cr(cogs, p["currency"], fx),
                    inr_wc=to_inr_cr(wc, p["currency"], fx),
                )
            )

            # Aging buckets — overdue share rises with DSO.
            overdue_weight = min(0.28, p["dso"] / 220)
            buckets = [
                ("0-30", 0.46, 0),
                ("31-60", 0.28, 0),
                ("61-90", 0.14, 1 if overdue_weight > 0.12 else 0),
                ("90+", overdue_weight + 0.12, 1),
            ]
            total_w = sum(b[1] for b in buckets)
            for label, w, overdue in buckets:
                amt = ar * (w / total_w)
                db.add(
                    Receivable(
                        country=code,
                        period=period,
                        bucket=label,
                        amount_local=amt,
                        amount_inr=to_inr_cr(amt, p["currency"], fx),
                        overdue=overdue,
                    )
                )

            pay_split = [
                ("current", 0.58, 18),
                ("due_soon", 0.27, 6),
                ("overdue", 0.15, -9),
            ]
            for status_p, w, days in pay_split:
                amt = ap * w
                db.add(
                    Payable(
                        country=code,
                        period=period,
                        status=status_p,
                        amount_local=amt,
                        amount_inr=to_inr_cr(amt, p["currency"], fx),
                        days_to_due=days,
                    )
                )

            # Calendar events
            events = [
                (date(period.year, period.month, 5), "payroll", "Payroll cycle", payroll, "users"),
                (date(period.year, period.month, min(28, period.day)), "supplier", "Supplier run", supplier, "truck"),
            ]
            if period.month in (3, 4, 9):
                events.append(
                    (date(period.year, period.month, 15), "taxes", "Tax remittance", taxes, "landmark")
                )
            if capex > inflow * 0.08:
                events.append(
                    (date(period.year, period.month, 12), "capex", "Capex drawdown", capex, "factory")
                )
            if customer > p["base_inflow"] * 1.12:
                events.append(
                    (date(period.year, period.month, 8), "receipt", "Large customer receipt", customer * 0.22, "arrow-down")
                )
            if debt_svc > 0:
                events.append(
                    (date(period.year, period.month, 20), "debt", "Debt service", debt_svc, "bank")
                )
            for ev_date, cat, label, amt, icon in events:
                db.add(
                    TreasuryEvent(
                        event_date=ev_date,
                        country=code,
                        category=cat,
                        label=label,
                        amount_local=amt,
                        amount_inr=to_inr_cr(amt, p["currency"], fx),
                        currency=p["currency"],
                        icon=icon,
                    )
                )

    # Daily slice for the as-of month — used by the cash calendar drill-in.
    as_of = date(2026, 9, 30)
    fx_spot = fx_for_month(32, rng)  # Sep 2026 is month index 32
    for code, p in COUNTRY_PROFILES.items():
        daily_open = books[code] * 0.98
        for d in range(1, 31):
            day = date(2026, 9, d)
            noise = float(rng.normal(1.0, 0.12))
            din = (p["base_inflow"] / 30) * noise
            dout = (p["base_inflow"] * p["outflow_ratio"] / 30) * float(rng.normal(1.0, 0.12))
            if d in (5, 20):
                dout *= 2.4  # payroll
            if d == 15:
                dout *= 1.6
            close = closing_cash(daily_open, din, dout)
            db.add(
                CashFlow(
                    country=code,
                    period=day,
                    granularity="day",
                    currency=p["currency"],
                    opening_cash=daily_open,
                    customer_receipts=din * 0.8,
                    ar_collections=din * 0.1,
                    intercompany_receipts=0.0,
                    interest_income=din * 0.02,
                    asset_sales=0.0,
                    other_inflows=din * 0.08,
                    supplier_payments=dout * 0.4,
                    payroll=dout * 0.25 if d in (5, 20) else dout * 0.05,
                    taxes=dout * 0.2 if d == 15 else 0.0,
                    rent=0.0,
                    capex=0.0,
                    debt_repayment=0.0,
                    interest_expense=dout * 0.02,
                    intercompany_transfers=0.0,
                    opex=dout * 0.3,
                    inflows=din,
                    outflows=dout,
                    closing_cash=close,
                    receivables=0,
                    payables=0,
                    inventory=0,
                    payroll_accrual=0,
                    taxes_accrual=0,
                    working_capital=0,
                    min_cash=p["min_cash"],
                    surplus_cash=max(0, close - p["min_cash"]),
                    funding_gap=max(0, p["min_cash"] - close),
                    invested_cash=0,
                    idle_cash=max(0, close - p["min_cash"]),
                    fx_exposure=0,
                    debt_service=0,
                    inr_inflows=to_inr_cr(din, p["currency"], fx_spot),
                    inr_outflows=to_inr_cr(dout, p["currency"], fx_spot),
                    inr_closing=to_inr_cr(close, p["currency"], fx_spot),
                    inr_idle=to_inr_cr(max(0, close - p["min_cash"]), p["currency"], fx_spot),
                    inr_funding=to_inr_cr(max(0, p["min_cash"] - close), p["currency"], fx_spot),
                    inr_fx_exposure=0,
                    inr_invested=0,
                    inr_min_cash=to_inr_cr(p["min_cash"], p["currency"], fx_spot),
                    business_unit=p["bu"],
                )
            )
            daily_open = close

    db.add_all(
        [
            AnalysisResult(key="annual_inflow_inr_2025", value=annual_inflow_inr, note="Simulated 2025 inflows, INR Cr"),
            AnalysisResult(key="annual_outflow_inr_2025", value=annual_outflow_inr, note="Simulated 2025 outflows, INR Cr"),
            AnalysisResult(key="as_of_index", value=32.0, note="Sep 2026 month index"),
        ]
    )
    db.commit()
