import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "POLICY" in r.json()["name"]


def test_markets(client):
    r = client.get("/api/markets")
    assert r.status_code == 200
    codes = {m["code"] for m in r.json()}
    assert codes == {"US", "IN", "UK", "EZ"}


def test_overview(client):
    r = client.get("/api/overview")
    assert r.status_code == 200
    body = r.json()
    assert len(body["kpis"]) == 4
    assert body["mood"]["code"]


def test_yield_curve_shape(client):
    r = client.get("/api/yield-curve", params={"market": "US"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) == 8
    assert body["shape"] in {"STEEP", "FLAT", "INVERTED", "NORMAL"}


def test_bond_lab(client):
    r = client.post(
        "/api/bond-lab",
        json={"face": 100, "coupon_rate": 0.04, "maturity_years": 10, "yield_rate": 0.04, "frequency": 2, "yield_shock_bp": 100},
    )
    assert r.status_code == 200
    body = r.json()
    assert abs(body["price"] - 100) < 0.02
    assert body["actual_price"] < body["price"]
    # convexity approx should beat duration-only for a +100 bp parallel
    assert abs(body["convexity_error"]) < abs(body["duration_error"])


def test_event_study(client):
    r = client.get("/api/event-study", params={"cb": "FED", "event_type": "HIKE", "window": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["n"] >= 1


def test_regression(client):
    r = client.post(
        "/api/regression",
        json={"dependent": "IN:10Y", "independents": ["US:10Y", "IN:policy"], "differences": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert "r_squared" in body
    assert len(body["warnings"]) >= 3


def test_scenario_disclaimer(client):
    r = client.post("/api/scenario", json={"fed_bp": -100})
    assert "NOT A FORECAST" in r.json()["disclaimer"]


def test_sources_are_demo(client):
    r = client.get("/api/sources")
    assert r.status_code == 200
    assert all(s["demo"] for s in r.json())
