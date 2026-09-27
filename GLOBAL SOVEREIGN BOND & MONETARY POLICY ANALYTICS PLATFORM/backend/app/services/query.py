from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from app.models.tables import (
    BondReturn,
    CentralBank,
    Country,
    MacroIndicator,
    PolicyEvent,
    PolicyRate,
    SovereignYield,
)

MARKET_MAP = {"US": "US", "IN": "IN", "UK": "UK", "EZ": "EZ", "EUROZONE": "EZ", "INDIA": "IN"}


def code(raw: str) -> str:
    return MARKET_MAP.get(raw.upper(), raw.upper())


def country_by_code(db: Session, c: str) -> Country:
    obj = db.query(Country).filter(Country.code == code(c)).one()
    return obj


def window_start(end: date, spec: str) -> date:
    spec = spec.upper()
    if spec == "1Y":
        return end - timedelta(days=365)
    if spec == "3Y":
        return end - timedelta(days=365 * 3)
    if spec == "5Y":
        return end - timedelta(days=365 * 5)
    if spec == "10Y":
        return end - timedelta(days=365 * 10)
    return date(2015, 1, 2)


def yield_frame(db: Session, market: str, maturity: str, start: date | None = None, end: date | None = None) -> pd.Series:
    c = country_by_code(db, market)
    q = db.query(SovereignYield).filter(SovereignYield.country_id == c.id, SovereignYield.maturity == maturity)
    if start:
        q = q.filter(SovereignYield.date >= start)
    if end:
        q = q.filter(SovereignYield.date <= end)
    rows = q.order_by(SovereignYield.date).all()
    if not rows:
        return pd.Series(dtype=float)
    return pd.Series({pd.Timestamp(r.date): r.value for r in rows}, name=f"{code(market)}_{maturity}")


def policy_frame(db: Session, market: str, start: date | None = None, end: date | None = None) -> pd.Series:
    c = country_by_code(db, market)
    cb = db.query(CentralBank).filter(CentralBank.country_id == c.id).one()
    q = db.query(PolicyRate).filter(PolicyRate.central_bank_id == cb.id)
    if start:
        q = q.filter(PolicyRate.date >= start)
    if end:
        q = q.filter(PolicyRate.date <= end)
    rows = q.order_by(PolicyRate.date).all()
    return pd.Series({pd.Timestamp(r.date): r.value for r in rows}, name=f"{code(market)}_POLICY")


def return_frame(db: Session, market: str, maturity: str = "10Y") -> pd.Series:
    c = country_by_code(db, market)
    rows = (
        db.query(BondReturn)
        .filter(BondReturn.country_id == c.id, BondReturn.maturity == maturity)
        .order_by(BondReturn.date)
        .all()
    )
    return pd.Series({pd.Timestamp(r.date): r.total_return for r in rows}, name=f"{code(market)}_{maturity}_TR")


def returns_components(db: Session, market: str, maturity: str = "10Y") -> pd.DataFrame:
    c = country_by_code(db, market)
    rows = (
        db.query(BondReturn)
        .filter(BondReturn.country_id == c.id, BondReturn.maturity == maturity)
        .order_by(BondReturn.date)
        .all()
    )
    return pd.DataFrame(
        {
            "date": [r.date for r in rows],
            "price_return": [r.price_return for r in rows],
            "coupon_return": [r.coupon_return for r in rows],
            "total_return": [r.total_return for r in rows],
        }
    ).set_index(pd.DatetimeIndex([r.date for r in rows]))


def macro_frame(db: Session, market: str, indicator: str) -> pd.Series:
    c = country_by_code(db, market)
    rows = (
        db.query(MacroIndicator)
        .filter(MacroIndicator.country_id == c.id, MacroIndicator.indicator == indicator)
        .order_by(MacroIndicator.date)
        .all()
    )
    return pd.Series({pd.Timestamp(r.date): r.value for r in rows}, name=f"{code(market)}_{indicator}")


def curve_on(db: Session, market: str, asof: date) -> dict[str, float]:
    c = country_by_code(db, market)
    # nearest available date ≤ asof
    row = (
        db.query(SovereignYield.date)
        .filter(SovereignYield.country_id == c.id, SovereignYield.date <= asof)
        .order_by(SovereignYield.date.desc())
        .first()
    )
    if not row:
        row = db.query(SovereignYield.date).filter(SovereignYield.country_id == c.id).order_by(SovereignYield.date.asc()).first()
    d = row[0]
    rows = db.query(SovereignYield).filter(SovereignYield.country_id == c.id, SovereignYield.date == d).all()
    return {"_date": d, **{r.maturity: r.value for r in rows}}


def policy_events(db: Session, cb_code: str | None = None):
    q = db.query(PolicyEvent, CentralBank).join(CentralBank, PolicyEvent.central_bank_id == CentralBank.id)
    if cb_code:
        q = q.filter(CentralBank.code == cb_code.upper())
    return q.order_by(PolicyEvent.date).all()
