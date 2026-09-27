from app.analytics.formulas import (
    borrowing_cost,
    cash_conversion_cycle,
    cash_released_from_days,
    cash_runway,
    closing_cash,
    convert_amount,
    dpo,
    dso,
    excess_cash,
    fx_convert,
    fx_shock_value,
    hedge_cost,
    hedge_residual,
    idle_cash,
    idle_cash_pct,
    interest_income,
    liquidity_efficiency_score,
    liquidity_gap,
    net_currency_exposure,
    pooling_benefit,
    reduction_pct,
    traffic_light,
    working_capital,
)


def test_closing_cash():
    assert closing_cash(100, 40, 25) == 115


def test_idle_cash_floors_at_zero():
    assert idle_cash(50, 60, 0) == 0
    assert idle_cash(100, 60, 10) == 30


def test_idle_cash_pct():
    assert idle_cash_pct(20, 100) == 0.2
    assert idle_cash_pct(10, 0) == 0


def test_liquidity_gap_sign():
    assert liquidity_gap(80, 20, 30, 60) == 10
    assert liquidity_gap(40, 10, 30, 50) < 0


def test_excess_cash_deficit():
    assert excess_cash(40, 60) == -20


def test_dso_dpo_ccc():
    assert round(dso(50, 400), 4) == round(50 / 400 * 365, 4)
    assert round(dpo(30, 300), 4) == round(30 / 300 * 365, 4)
    assert cash_conversion_cycle(45, 40, 35) == 50


def test_dso_zero_revenue():
    assert dso(10, 0) == 0
    assert dpo(10, 0) == 0


def test_cash_released_from_dso():
    # 5 days on ₹365 Cr revenue → ₹5 Cr
    assert cash_released_from_days(5, 365) == 5


def test_working_capital():
    assert working_capital(80, 40, 30) == 90


def test_fx_convert_and_cross():
    assert fx_convert(10, 83.5) == 835
    usd = convert_amount(10, 83.5, 83.5)
    assert round(usd, 6) == 10
    gbp = convert_amount(10, 83.5, 106)
    assert round(gbp, 4) == round(835 / 106, 4)


def test_fx_shock():
    assert fx_shock_value(100, 83, 0.10) == 100 * 83 * 1.1


def test_interest_and_borrowing():
    assert interest_income(100, 0.06, 0.5) == 3
    assert borrowing_cost(50, 0.08, 1) == 4


def test_pooling_benefit():
    assert pooling_benefit(5, 2, 1) == 6


def test_cash_runway():
    assert cash_runway(90, 3) == 30
    assert cash_runway(90, 0) == 0


def test_natural_hedge_and_hedge_residual():
    assert net_currency_exposure(40, 25) == 15
    assert hedge_residual(100, 0.5) == 50
    assert hedge_residual(100, 1.5) == 0
    assert hedge_cost(100, 0.5, 100) == 0.5  # 100 bps = 1%


def test_traffic_light():
    assert traffic_light(0.20, 0, 100) == "SAFE"
    assert traffic_light(0.05, 0, 100) == "WATCH"
    assert traffic_light(0, 10, 100) == "TIGHT"
    assert traffic_light(0, 20, 100) == "FUNDING_REQUIRED"


def test_efficiency_score_bounds():
    s = liquidity_efficiency_score(0.8, 0.1, 0.05, 0.2, 0.1, 0.7)
    assert 0 <= s <= 100


def test_reduction_pct():
    assert abs(reduction_pct(100, 88) - 0.12) < 1e-9
    assert reduction_pct(0, 1) == 0
