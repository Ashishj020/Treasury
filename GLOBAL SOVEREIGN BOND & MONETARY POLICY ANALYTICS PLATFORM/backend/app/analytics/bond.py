"""Closed-form fixed-income analytics. All rates are decimal (0.04 = 4%)."""

from __future__ import annotations

import math


def _periods(maturity_years: float, frequency: int) -> int:
    if frequency <= 0:
        raise ValueError("frequency must be positive")
    n = int(round(maturity_years * frequency))
    if n < 1:
        raise ValueError("maturity must produce at least one period")
    return n


def bond_price(
    face: float,
    coupon_rate: float,
    yield_rate: float,
    maturity_years: float,
    frequency: int = 2,
) -> float:
    """Price of a fixed coupon bond using standard present-value identity."""
    n = _periods(maturity_years, frequency)
    c = face * coupon_rate / frequency
    r = yield_rate / frequency
    if abs(r) < 1e-15:
        return face + c * n
    pv_coupons = c * (1 - (1 + r) ** (-n)) / r
    pv_face = face / (1 + r) ** n
    return pv_coupons + pv_face


def current_yield(face: float, coupon_rate: float, price: float) -> float:
    if price == 0:
        raise ValueError("price must be non-zero")
    return (face * coupon_rate) / price


def macaulay_duration(
    face: float,
    coupon_rate: float,
    yield_rate: float,
    maturity_years: float,
    frequency: int = 2,
) -> float:
    """Macaulay duration in years — weighted average time to cash flows."""
    n = _periods(maturity_years, frequency)
    c = face * coupon_rate / frequency
    r = yield_rate / frequency
    price = bond_price(face, coupon_rate, yield_rate, maturity_years, frequency)
    if price == 0:
        raise ValueError("price must be non-zero")
    weighted = 0.0
    for t in range(1, n + 1):
        cf = c if t < n else c + face
        df = (1 + r) ** (-t)
        weighted += (t / frequency) * cf * df
    return weighted / price


def modified_duration(
    face: float,
    coupon_rate: float,
    yield_rate: float,
    maturity_years: float,
    frequency: int = 2,
) -> float:
    mac = macaulay_duration(face, coupon_rate, yield_rate, maturity_years, frequency)
    return mac / (1 + yield_rate / frequency)


def convexity(
    face: float,
    coupon_rate: float,
    yield_rate: float,
    maturity_years: float,
    frequency: int = 2,
) -> float:
    """Annual convexity: second derivative of price w.r.t. yield, scaled by 1/P."""
    n = _periods(maturity_years, frequency)
    c = face * coupon_rate / frequency
    r = yield_rate / frequency
    price = bond_price(face, coupon_rate, yield_rate, maturity_years, frequency)
    if price == 0:
        raise ValueError("price must be non-zero")
    acc = 0.0
    for t in range(1, n + 1):
        cf = c if t < n else c + face
        acc += cf * t * (t + 1) / ((1 + r) ** (t + 2))
    return acc / (price * frequency**2)


def duration_price_change(price: float, mod_dur: float, dy: float, conv: float | None = None) -> float:
    """First-order (and optional second-order) Taylor approximation of ΔP."""
    linear = -mod_dur * price * dy
    if conv is None:
        return linear
    return linear + 0.5 * conv * price * dy**2


def total_return_from_yields(
    y_prev: float,
    y_now: float,
    coupon_rate: float,
    maturity_years: float,
    dt_years: float = 1 / 252,
    frequency: int = 2,
    face: float = 100.0,
) -> dict[str, float]:
    """One-period total return of a constant-maturity par-ish coupon bond."""
    p0 = bond_price(face, coupon_rate, y_prev, maturity_years, frequency)
    remaining = max(maturity_years - dt_years, 1 / frequency)
    p1 = bond_price(face, coupon_rate, y_now, remaining, frequency)
    coupon = coupon_rate * dt_years * face
    price_ret = (p1 - p0) / p0
    coupon_ret = coupon / p0
    return {
        "price_return": price_ret,
        "coupon_return": coupon_ret,
        "total_return": price_ret + coupon_ret,
        "price_t0": p0,
        "price_t1": p1,
    }


def nelson_siegel(tau: float, b0: float, b1: float, b2: float, lam: float = 1.4) -> float:
    if tau <= 0:
        return b0 + b1
    x = tau / lam
    a1 = (1 - math.exp(-x)) / x
    a2 = a1 - math.exp(-x)
    return b0 + b1 * a1 + b2 * a2


def classify_curve(spread_2s10s: float) -> tuple[str, str]:
    """Transparent slope taxonomy used throughout the lab."""
    if spread_2s10s < -0.15:
        return "INVERTED", "The Recession Alarm"
    if spread_2s10s < 0.20:
        return "FLAT", "The Nervous One"
    if spread_2s10s > 1.20:
        return "STEEP", "The Growth Bet"
    return "NORMAL", "The Optimist"


def classify_policy_regime(change_90d_bp: float, qe: bool, qt: bool) -> str:
    if qt and change_90d_bp >= 0:
        return "HAWKISH"
    if qe and change_90d_bp <= 0:
        return "DOVISH"
    if change_90d_bp >= 25:
        return "HAWKISH"
    if change_90d_bp <= -25:
        return "DOVISH"
    return "NEUTRAL"


def classify_policy_cycle(change_180d_bp: float, level: float, peak: float) -> str:
    if change_180d_bp >= 50:
        return "HIKING"
    if change_180d_bp <= -50:
        return "CUTTING"
    if abs(level - peak) <= 0.15 and level >= peak - 0.25:
        return "PEAK"
    return "NEUTRAL"
