"""Simplified project-model formulas for the treasury lab.

These are educational, not bank-grade treasury calculations.
Every function is pure and unit-tested.
"""

from __future__ import annotations

from typing import Iterable


def closing_cash(opening: float, inflows: float, outflows: float) -> float:
    """Closing Cash = Opening Cash + Cash Inflows − Cash Outflows."""
    return opening + inflows - outflows


def excess_cash(closing: float, min_required: float) -> float:
    """Excess Cash = Closing Cash − Minimum Required Cash.

    Negative values are a liquidity deficit / funding requirement.
    """
    return closing - min_required


def idle_cash(closing: float, operating_required: float, invested: float = 0.0) -> float:
    """Idle cash is cash above the operating requirement that is not deployed.

    Idle Cash = max(0, Closing Cash − Required Operating Cash − Invested Cash)
    """
    return max(0.0, closing - operating_required - invested)


def idle_cash_pct(idle: float, total_cash: float) -> float:
    if total_cash <= 0:
        return 0.0
    return idle / total_cash


def liquidity_gap(
    available: float,
    expected_inflows: float,
    expected_outflows: float,
    min_required: float,
) -> float:
    """Liquidity Gap = Available + Expected Inflows − Expected Outflows − Min Cash.

    Positive = surplus. Negative = funding requirement.
    """
    return available + expected_inflows - expected_outflows - min_required


def working_capital(receivables: float, inventory: float, payables: float) -> float:
    """Working Capital = Receivables + Inventory − Payables."""
    return receivables + inventory - payables


def dso(avg_ar: float, revenue: float, days: float = 365.0) -> float:
    """DSO = Average Accounts Receivable / Revenue × 365."""
    if revenue <= 0:
        return 0.0
    return avg_ar / revenue * days


def dpo(avg_ap: float, cogs: float, days: float = 365.0) -> float:
    """DPO = Average Accounts Payable / Cost of Goods Sold × 365."""
    if cogs <= 0:
        return 0.0
    return avg_ap / cogs * days


def inventory_days(avg_inventory: float, cogs: float, days: float = 365.0) -> float:
    """Inventory Days = Average Inventory / COGS × 365."""
    if cogs <= 0:
        return 0.0
    return avg_inventory / cogs * days


def cash_conversion_cycle(dso_days: float, inv_days: float, dpo_days: float) -> float:
    """CCC = DSO + Inventory Days − DPO."""
    return dso_days + inv_days - dpo_days


def cash_released_from_days(delta_days: float, annual_flow: float, days: float = 365.0) -> float:
    """Cash released (positive) or absorbed (negative) from a days-ratio change.

    Reducing DSO by 5 days releases ≈ Revenue × 5 / 365.
    Increasing DPO by 5 days also releases cash.
    Reducing inventory days releases cash.
    """
    if days <= 0:
        return 0.0
    return annual_flow * delta_days / days


def fx_convert(amount: float, rate: float) -> float:
    """INR Value = Foreign Currency Amount × FX Rate (project convention)."""
    return amount * rate


def convert_amount(amount: float, from_rate_vs_inr: float, to_rate_vs_inr: float) -> float:
    """Convert an amount quoted in one currency into another via INR cross."""
    if from_rate_vs_inr <= 0:
        return 0.0
    inr = amount * from_rate_vs_inr
    if to_rate_vs_inr <= 0:
        return inr
    return inr / to_rate_vs_inr


def interest_income(amount: float, annual_yield: float, time_years: float) -> float:
    """Interest Income = Invested Amount × Annual Yield × Time."""
    return amount * annual_yield * time_years


def borrowing_cost(amount: float, rate: float, time_years: float) -> float:
    """Interest Expense = Borrowing Amount × Interest Rate × Time."""
    return amount * rate * time_years


def pooling_benefit(
    avoided_borrow_cost: float,
    additional_investment_income: float,
    pooling_costs: float,
) -> float:
    """Pooling Benefit = Avoided Borrowing Cost + Additional Investment Income − Pooling Costs."""
    return avoided_borrow_cost + additional_investment_income - pooling_costs


def cash_runway(available_cash: float, avg_daily_outflow: float) -> float:
    """Cash Runway (days) = Available Cash / Average Daily Cash Outflow."""
    if avg_daily_outflow <= 0:
        return 0.0
    return available_cash / avg_daily_outflow


def fx_shock_value(amount: float, rate: float, shock_pct: float) -> float:
    """Revalue an FX-exposed amount after a percentage rate shock."""
    return amount * rate * (1.0 + shock_pct)


def net_currency_exposure(inflows: float, outflows: float) -> float:
    """Net Exposure = Currency Inflows − Currency Outflows (natural hedge)."""
    return inflows - outflows


def hedge_residual(exposure: float, hedge_ratio: float) -> float:
    """Residual exposure after applying a hedge ratio in [0, 1]."""
    ratio = min(1.0, max(0.0, hedge_ratio))
    return exposure * (1.0 - ratio)


def hedge_cost(exposure: float, hedge_ratio: float, cost_bps: float) -> float:
    """Illustrative hedging cost = |exposure| × hedge ratio × cost in decimal (bps/10000)."""
    ratio = min(1.0, max(0.0, hedge_ratio))
    return abs(exposure) * ratio * cost_bps / 10000.0


def weighted_score(values: dict[str, float], weights: dict[str, float]) -> float:
    """Weighted average of normalized 0–100 component scores."""
    total_w = sum(max(0.0, w) for w in weights.values())
    if total_w <= 0:
        return 0.0
    acc = 0.0
    for key, weight in weights.items():
        acc += values.get(key, 0.0) * max(0.0, weight)
    return acc / total_w


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def liquidity_efficiency_score(
    cash_utilization: float,
    idle_cash_ratio: float,
    funding_dependency: float,
    investment_deployment: float,
    fx_exposure_ratio: float,
    wc_efficiency: float,
) -> float:
    """Project-defined 0–100 Liquidity Efficiency Score.

    Not an established industry metric. Higher is better.
    """
    util = clamp(cash_utilization * 100)
    idle_pen = clamp(100 - idle_cash_ratio * 220)
    fund_pen = clamp(100 - funding_dependency * 180)
    invest = clamp(investment_deployment * 100)
    fx_pen = clamp(100 - fx_exposure_ratio * 90)
    wc = clamp(wc_efficiency * 100)
    return round(
        0.22 * util
        + 0.22 * idle_pen
        + 0.16 * fund_pen
        + 0.14 * invest
        + 0.12 * fx_pen
        + 0.14 * wc,
        1,
    )


def traffic_light(surplus_ratio: float, funding_gap: float, min_cash: float) -> str:
    """Transparent liquidity status from surplus ratio and funding gap.

    SAFE: surplus ≥ 15% of min cash and no funding gap
    WATCH: surplus 0–15% of min cash
    TIGHT: deficit up to 15% of min cash
    FUNDING_REQUIRED: deficit > 15% of min cash
    """
    if min_cash <= 0:
        return "WATCH"
    if funding_gap > 0.15 * min_cash:
        return "FUNDING_REQUIRED"
    if funding_gap > 0:
        return "TIGHT"
    if surplus_ratio < 0.15:
        return "WATCH"
    return "SAFE"


def mean(values: Iterable[float]) -> float:
    seq = list(values)
    if not seq:
        return 0.0
    return sum(seq) / len(seq)


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current - previous) / abs(previous)


def reduction_pct(baseline: float, optimized: float) -> float:
    if baseline == 0:
        return 0.0
    return (baseline - optimized) / baseline
