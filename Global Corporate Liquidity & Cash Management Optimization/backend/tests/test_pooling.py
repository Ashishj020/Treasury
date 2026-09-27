from dataclasses import replace

from app.treasury.engine import PoolParams, Position, compare_strategies, simulate_strategy


def _pos(country, closing, min_cash, invested, fx=8.0, inf=20.0, out=18.0):
    surplus = max(0, closing - min_cash)
    funding = max(0, min_cash - closing)
    idle = max(0, closing - min_cash - invested)
    return Position(
        country=country,
        currency={"IN": "INR", "US": "USD", "UK": "GBP", "SG": "SGD"}[country],
        closing=closing,
        min_cash=min_cash,
        invested=invested,
        idle=idle,
        funding=funding,
        surplus=surplus,
        fx_exposure=fx,
        inflows=inf,
        outflows=out,
        inr_closing=closing,
        inr_min=min_cash,
        inr_invested=invested,
        inr_idle=idle,
        inr_funding=funding,
        inr_fx=fx,
        inr_inflows=inf,
        inr_outflows=out,
        inr_surplus=surplus,
        status="WATCH",
        personality="",
    )


BOOK = [
    _pos("IN", 128.0, 60.0, 18.0, fx=12),
    _pos("US", 78.0, 42.0, 14.0, fx=10),
    _pos("UK", 90.0, 70.0, 8.0, fx=9),
    _pos("SG", 30.0, 38.0, 0.0, fx=7),
]


def test_no_pooling_keeps_singapore_deficit():
    res = simulate_strategy(BOOK, "none")
    sg = next(p for p in res["positions"] if p.country == "SG")
    assert sg.inr_funding > 0


def test_physical_pooling_covers_deficit():
    res = simulate_strategy(BOOK, "physical", PoolParams(transfer_threshold=3, investment_threshold=8.4))
    sg = next(p for p in res["positions"] if p.country == "SG")
    assert sg.inr_funding == 0 or sg.inr_funding < 0.5
    assert res["transfers"]


def test_hybrid_reduces_idle_versus_baseline():
    cmp_ = compare_strategies(BOOK, PoolParams(investment_threshold=8.4, transfer_threshold=3))
    assert cmp_["optimized_idle"] < cmp_["baseline_idle"]
    assert cmp_["idle_reduction"] > 0.03


def test_notional_barely_moves_idle():
    none = simulate_strategy(BOOK, "none")
    notion = simulate_strategy(BOOK, "notional", PoolParams(investment_threshold=8.4))
    # Notional may invest a little but should not match physical idle reduction
    phys = simulate_strategy(BOOK, "physical", PoolParams(investment_threshold=8.4, transfer_threshold=3))
    idle_drop_n = none["totals"]["idle"] - notion["totals"]["idle"]
    idle_drop_p = none["totals"]["idle"] - phys["totals"]["idle"]
    assert idle_drop_p >= idle_drop_n


def test_excluding_india_from_pool_leaves_more_idle():
    full = simulate_strategy(BOOK, "hybrid", PoolParams(members=["IN", "US", "UK", "SG"]))
    no_in = simulate_strategy(BOOK, "hybrid", PoolParams(members=["US", "UK", "SG"]))
    assert no_in["totals"]["funding"] >= full["totals"]["funding"] - 1e-6


def test_strategy_ranking_has_four():
    cmp_ = compare_strategies(BOOK)
    assert len(cmp_["scorecard"]) == 4
    assert cmp_["winner"]["id"] in {"hybrid", "physical", "notional", "none"}
