from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    region: Mapped[str] = mapped_column(String(40))
    currency: Mapped[str] = mapped_column(String(8))
    benchmark_label: Mapped[str] = mapped_column(String(120))

    central_bank: Mapped["CentralBank"] = relationship(back_populates="country", uselist=False)


class CentralBank(Base):
    __tablename__ = "central_banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    code: Mapped[str] = mapped_column(String(8), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    policy_rate_name: Mapped[str] = mapped_column(String(80))

    country: Mapped[Country] = relationship(back_populates="central_bank")


class PolicyRate(Base):
    __tablename__ = "policy_rates"
    __table_args__ = (UniqueConstraint("central_bank_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    central_bank_id: Mapped[int] = mapped_column(ForeignKey("central_banks.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="DEMO")
    frequency: Mapped[str] = mapped_column(String(16), default="daily")


class SovereignYield(Base):
    __tablename__ = "sovereign_yields"
    __table_args__ = (UniqueConstraint("country_id", "date", "maturity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    maturity: Mapped[str] = mapped_column(String(8), index=True)
    instrument: Mapped[str] = mapped_column(String(80))
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="DEMO")
    frequency: Mapped[str] = mapped_column(String(16), default="daily")


class BondReturn(Base):
    __tablename__ = "bond_returns"
    __table_args__ = (UniqueConstraint("country_id", "date", "maturity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    maturity: Mapped[str] = mapped_column(String(8))
    price_return: Mapped[float] = mapped_column(Float)
    coupon_return: Mapped[float] = mapped_column(Float)
    total_return: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="DEMO")
    frequency: Mapped[str] = mapped_column(String(16), default="daily")


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"
    __table_args__ = (UniqueConstraint("country_id", "date", "indicator"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    indicator: Mapped[str] = mapped_column(String(40), index=True)
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="DEMO")
    frequency: Mapped[str] = mapped_column(String(16), default="monthly")


class PolicyEvent(Base):
    __tablename__ = "policy_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    central_bank_id: Mapped[int] = mapped_column(ForeignKey("central_banks.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    policy_rate: Mapped[float] = mapped_column(Float)
    change_bp: Mapped[float] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(80))
    rationale: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(40), default="DEMO")


class MarketEvent(Base):
    __tablename__ = "market_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    markets: Mapped[str] = mapped_column(String(80))


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    institution: Mapped[str] = mapped_column(String(160))
    variable: Mapped[str] = mapped_column(String(160))
    frequency: Mapped[str] = mapped_column(String(32))
    date_range: Mapped[str] = mapped_column(String(80))
    transformation: Mapped[str] = mapped_column(Text)
    methodology: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(240))
    demo: Mapped[int] = mapped_column(Integer, default=1)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    payload: Mapped[str] = mapped_column(Text)
