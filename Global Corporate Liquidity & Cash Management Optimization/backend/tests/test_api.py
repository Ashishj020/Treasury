from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analytics.formulas import reduction_pct
from app.database import SessionLocal
from app.data.generate import seed
from app.main import app
from app.models.entities import CashFlow, Country
from app.treasury.engine import compare_strategies, positions_at


client = TestClient(app)


def setup_module():
    db = SessionLocal()
    try:
        seed(db, 42)
    finally:
        db.close()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert "SIMULATED" in r.json()["disclaimer"]


def test_countries():
    r = client.get("/api/countries")
    assert r.status_code == 200
    codes = {c["code"] for c in r.json()}
    assert codes == {"IN", "US", "UK", "SG"}


def test_annual_cash_flow_exceeds_500cr():
    db = SessionLocal()
    try:
        rows = (
            db.query(CashFlow)
            .filter(
                CashFlow.granularity == "month",
                CashFlow.period >= date(2025, 1, 1),
                CashFlow.period <= date(2025, 12, 31),
            )
            .all()
        )
        gross = sum(r.inr_inflows + r.inr_outflows for r in rows)
        inf = sum(r.inr_inflows for r in rows)
        assert inf > 500
        assert gross > 500
    finally:
        db.close()


def test_overview_kpis():
    r = client.get("/api/overview", params={"reporting": "INR", "strategy": "none"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["kpis"]) == 8
    assert data["annual_flow_inr"]["inflows"] > 500


def test_reporting_currency_changes_magnitude():
    inr = client.get("/api/overview", params={"reporting": "INR"}).json()
    usd = client.get("/api/overview", params={"reporting": "USD"}).json()
    inr_cash = next(k for k in inr["kpis"] if k["key"] == "cash")["value"]
    usd_cash = next(k for k in usd["kpis"] if k["key"] == "cash")["value"]
    assert inr_cash != usd_cash
    assert usd_cash < inr_cash  # millions of USD vs crore INR, still typically smaller count


def test_optimize_idle_reduction_near_12pct():
    db = SessionLocal()
    try:
        pos = positions_at(db)
        cmp_ = compare_strategies(pos)
        red = cmp_["idle_reduction"]
        assert 0.10 <= red <= 0.15, f"idle reduction {red:.3%} not near 12%"
    finally:
        db.close()


def test_working_capital_and_fx_endpoints():
    assert client.get("/api/working-capital").status_code == 200
    assert client.get("/api/receivables").status_code == 200
    assert client.get("/api/payables").status_code == 200
    assert client.get("/api/fx").status_code == 200
    assert client.get("/api/pooling", params={"strategy": "hybrid"}).status_code == 200
    assert client.get("/api/methodology").status_code == 200


def test_scenario_stress_worsens_funding():
    base = client.post("/api/scenario", json={"scenario": "base"}).json()
    stress = client.post("/api/scenario", json={"scenario": "stressed"}).json()
    assert stress["after"]["funding"] >= base["after"]["funding"] - 1e-6


def test_reduction_formula_used():
    assert abs(reduction_pct(84, 73.92) - 0.12) < 1e-9
