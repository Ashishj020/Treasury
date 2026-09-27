from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.entities import CashFlow, Country, Currency, ExchangeRate


AS_OF = date(2026, 9, 30)


def latest_fx_map(db: Session, as_of: date | None = None) -> dict[str, float]:
    as_of = as_of or AS_OF
    rows = (
        db.query(ExchangeRate)
        .filter(ExchangeRate.as_of <= as_of)
        .order_by(ExchangeRate.as_of.desc())
        .all()
    )
    out: dict[str, float] = {}
    for row in rows:
        if row.pair not in out:
            out[row.pair] = row.rate
    return out


def inr_per_unit(currency: str, fx: dict[str, float]) -> float:
    if currency == "INR":
        return 1.0
    key = f"{currency}INR"
    return fx.get(key, 1.0)


def convert_inr_cr(amount_inr_cr: float, reporting: str, fx: dict[str, float]) -> float:
    if reporting == "INR":
        return amount_inr_cr
    rate = inr_per_unit(reporting, fx)
    if rate <= 0:
        return amount_inr_cr
    # INR Cr → foreign millions: (cr * 10) / fx
    return amount_inr_cr * 10.0 / rate


def symbol_for(reporting: str) -> str:
    return {"INR": "₹", "USD": "$", "GBP": "£", "SGD": "S$"}.get(reporting, reporting)


def unit_for(reporting: str) -> str:
    return "Cr" if reporting == "INR" else "mn"


def monthly_rows(
    db: Session,
    country: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> list[CashFlow]:
    q = db.query(CashFlow).filter(CashFlow.granularity == "month")
    if country and country not in ("ALL", "GLOBAL"):
        q = q.filter(CashFlow.country == country)
    if start:
        q = q.filter(CashFlow.period >= start)
    if end:
        q = q.filter(CashFlow.period <= end)
    return q.order_by(CashFlow.period, CashFlow.country).all()


def snapshot_rows(db: Session, as_of: date | None = None) -> list[CashFlow]:
    as_of = as_of or AS_OF
    return (
        db.query(CashFlow)
        .filter(CashFlow.granularity == "month", CashFlow.period == as_of)
        .all()
    )


def countries_map(db: Session) -> dict[str, Country]:
    return {c.code: c for c in db.query(Country).all()}


def currencies_map(db: Session) -> dict[str, Currency]:
    return {c.code: c for c in db.query(Currency).all()}
