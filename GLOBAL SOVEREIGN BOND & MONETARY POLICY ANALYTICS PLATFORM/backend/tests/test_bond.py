from app.analytics.bond import (
    bond_price,
    classify_curve,
    convexity,
    macaulay_duration,
    modified_duration,
    nelson_siegel,
)


def test_par_bond_prices_near_face():
    p = bond_price(100, 0.05, 0.05, 10, 2)
    assert abs(p - 100) < 1e-6


def test_price_falls_when_yield_rises():
    p0 = bond_price(100, 0.04, 0.04, 10, 2)
    p1 = bond_price(100, 0.04, 0.05, 10, 2)
    assert p1 < p0


def test_zero_yield_is_undiscounted_cashflows():
    p = bond_price(100, 0.04, 0.0, 2, 2)
    assert abs(p - (2 + 2 + 2 + 102)) < 1e-8


def test_macaulay_of_zero_equals_maturity():
    d = macaulay_duration(100, 0.0, 0.05, 10, 1)
    assert abs(d - 10) < 1e-6


def test_modified_duration_identity():
    mac = macaulay_duration(100, 0.04, 0.05, 10, 2)
    mod = modified_duration(100, 0.04, 0.05, 10, 2)
    assert abs(mod - mac / (1 + 0.05 / 2)) < 1e-10


def test_convexity_positive():
    assert convexity(100, 0.04, 0.05, 10, 2) > 0


def test_classify_curve():
    assert classify_curve(-0.4)[0] == "INVERTED"
    assert classify_curve(0.05)[0] == "FLAT"
    assert classify_curve(1.5)[0] == "STEEP"
    assert classify_curve(0.6)[0] == "NORMAL"


def test_nelson_siegel_short_equals_b0_plus_b1():
    assert abs(nelson_siegel(0.0, 3, -1, 0.5) - 2) < 1e-9


def test_invalid_frequency():
    try:
        bond_price(100, 0.04, 0.04, 10, 0)
        assert False
    except ValueError:
        pass
