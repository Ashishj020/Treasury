from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(8))
    region: Mapped[str] = mapped_column(String(64))
    personality: Mapped[str] = mapped_column(String(64))
    flag: Mapped[str] = mapped_column(String(8))
    headquarters: Mapped[int] = mapped_column(Integer, default=0)
    min_cash_local: Mapped[float] = mapped_column(Float)
    dso: Mapped[float] = mapped_column(Float)
    dpo: Mapped[float] = mapped_column(Float)
    inventory_days: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    symbol: Mapped[str] = mapped_column(String(8))
    inr_per_unit_base: Mapped[float] = mapped_column(Float)


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    as_of: Mapped[date] = mapped_column(Date, index=True)
    pair: Mapped[str] = mapped_column(String(16), index=True)
    rate: Mapped[float] = mapped_column(Float)


class CashFlow(Base):
    __tablename__ = "cash_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(8), ForeignKey("countries.code"), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    granularity: Mapped[str] = mapped_column(String(16), default="month")
    currency: Mapped[str] = mapped_column(String(8))
    opening_cash: Mapped[float] = mapped_column(Float)
    customer_receipts: Mapped[float] = mapped_column(Float)
    ar_collections: Mapped[float] = mapped_column(Float)
    intercompany_receipts: Mapped[float] = mapped_column(Float)
    interest_income: Mapped[float] = mapped_column(Float)
    asset_sales: Mapped[float] = mapped_column(Float)
    other_inflows: Mapped[float] = mapped_column(Float)
    supplier_payments: Mapped[float] = mapped_column(Float)
    payroll: Mapped[float] = mapped_column(Float)
    taxes: Mapped[float] = mapped_column(Float)
    rent: Mapped[float] = mapped_column(Float)
    capex: Mapped[float] = mapped_column(Float)
    debt_repayment: Mapped[float] = mapped_column(Float)
    interest_expense: Mapped[float] = mapped_column(Float)
    intercompany_transfers: Mapped[float] = mapped_column(Float)
    opex: Mapped[float] = mapped_column(Float)
    inflows: Mapped[float] = mapped_column(Float)
    outflows: Mapped[float] = mapped_column(Float)
    closing_cash: Mapped[float] = mapped_column(Float)
    receivables: Mapped[float] = mapped_column(Float)
    payables: Mapped[float] = mapped_column(Float)
    inventory: Mapped[float] = mapped_column(Float)
    payroll_accrual: Mapped[float] = mapped_column(Float)
    taxes_accrual: Mapped[float] = mapped_column(Float)
    working_capital: Mapped[float] = mapped_column(Float)
    min_cash: Mapped[float] = mapped_column(Float)
    surplus_cash: Mapped[float] = mapped_column(Float)
    funding_gap: Mapped[float] = mapped_column(Float)
    invested_cash: Mapped[float] = mapped_column(Float)
    idle_cash: Mapped[float] = mapped_column(Float)
    fx_exposure: Mapped[float] = mapped_column(Float)
    debt_service: Mapped[float] = mapped_column(Float)
    inr_inflows: Mapped[float] = mapped_column(Float)
    inr_outflows: Mapped[float] = mapped_column(Float)
    inr_closing: Mapped[float] = mapped_column(Float)
    inr_idle: Mapped[float] = mapped_column(Float)
    inr_funding: Mapped[float] = mapped_column(Float)
    inr_fx_exposure: Mapped[float] = mapped_column(Float)
    inr_invested: Mapped[float] = mapped_column(Float)
    inr_min_cash: Mapped[float] = mapped_column(Float)
    business_unit: Mapped[str] = mapped_column(String(32), default="Operations")


class Receivable(Base):
    __tablename__ = "receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    bucket: Mapped[str] = mapped_column(String(16))
    amount_local: Mapped[float] = mapped_column(Float)
    amount_inr: Mapped[float] = mapped_column(Float)
    overdue: Mapped[int] = mapped_column(Integer, default=0)


class Payable(Base):
    __tablename__ = "payables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(16))
    amount_local: Mapped[float] = mapped_column(Float)
    amount_inr: Mapped[float] = mapped_column(Float)
    days_to_due: Mapped[int] = mapped_column(Integer, default=0)


class WorkingCapitalRow(Base):
    __tablename__ = "working_capital"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    revenue: Mapped[float] = mapped_column(Float)
    cogs: Mapped[float] = mapped_column(Float)
    ar: Mapped[float] = mapped_column(Float)
    ap: Mapped[float] = mapped_column(Float)
    inventory: Mapped[float] = mapped_column(Float)
    dso: Mapped[float] = mapped_column(Float)
    dpo: Mapped[float] = mapped_column(Float)
    inventory_days: Mapped[float] = mapped_column(Float)
    ccc: Mapped[float] = mapped_column(Float)
    wc: Mapped[float] = mapped_column(Float)
    inr_revenue: Mapped[float] = mapped_column(Float)
    inr_cogs: Mapped[float] = mapped_column(Float)
    inr_wc: Mapped[float] = mapped_column(Float)


class LiquidityPosition(Base):
    __tablename__ = "liquidity_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    opening: Mapped[float] = mapped_column(Float)
    closing: Mapped[float] = mapped_column(Float)
    min_cash: Mapped[float] = mapped_column(Float)
    surplus: Mapped[float] = mapped_column(Float)
    funding: Mapped[float] = mapped_column(Float)
    idle: Mapped[float] = mapped_column(Float)
    invested: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(24))
    inr_closing: Mapped[float] = mapped_column(Float)
    inr_idle: Mapped[float] = mapped_column(Float)
    inr_funding: Mapped[float] = mapped_column(Float)
    inr_surplus: Mapped[float] = mapped_column(Float)


class InvestmentOption(Base):
    __tablename__ = "investment_options"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    horizon_days: Mapped[int] = mapped_column(Integer)
    yield_pct: Mapped[float] = mapped_column(Float)
    liquidity_score: Mapped[int] = mapped_column(Integer)
    risk_note: Mapped[str] = mapped_column(Text)


class BorrowingFacility(Base):
    __tablename__ = "borrowings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(8))
    rate_pct: Mapped[float] = mapped_column(Float)
    tenor_days: Mapped[int] = mapped_column(Integer)
    limit_local: Mapped[float] = mapped_column(Float)
    drawn_local: Mapped[float] = mapped_column(Float)
    country: Mapped[str] = mapped_column(String(8))
    notes: Mapped[str] = mapped_column(Text, default="")


class PoolingStrategy(Base):
    __tablename__ = "cash_pooling_strategies"

    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    complexity: Mapped[int] = mapped_column(Integer)
    fx_friction: Mapped[float] = mapped_column(Float)
    transfer_cost_bps: Mapped[float] = mapped_column(Float)


class ScenarioDef(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    collection_factor: Mapped[float] = mapped_column(Float)
    outflow_factor: Mapped[float] = mapped_column(Float)
    rate_shift_bp: Mapped[float] = mapped_column(Float)
    fx_inr_shock: Mapped[float] = mapped_column(Float)
    receivable_delay_days: Mapped[int] = mapped_column(Integer, default=0)


class TreasuryEvent(Base):
    __tablename__ = "treasury_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    category: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(128))
    amount_local: Mapped[float] = mapped_column(Float)
    amount_inr: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8))
    icon: Mapped[str] = mapped_column(String(24))


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(Text, default="")
