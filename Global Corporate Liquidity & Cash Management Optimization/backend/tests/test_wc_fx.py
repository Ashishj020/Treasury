import pytest

from app.analytics.formulas import cash_conversion_cycle, dpo, dso, inventory_days


@pytest.mark.parametrize("ar,rev", [(0, 100), (50, 0), (80, 400)])
def test_dso_edge(ar, rev):
    val = dso(ar, rev)
    assert val >= 0


def test_ccc_negative_possible():
    # High DPO can make CCC negative — that's a real working-capital shape.
    assert cash_conversion_cycle(20, 10, 45) == -15


def test_inventory_days():
    assert inventory_days(40, 365) == 40
