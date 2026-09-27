from sqlalchemy.orm import Session

from app.analytics.formulas import fx_shock_value, hedge_cost, hedge_residual, net_currency_exposure
from app.models.entities import CashFlow, ExchangeRate
from app.treasury.engine import positions_at, reporting_meta, simulate_strategy
from app.utils.fx import AS_OF, convert_inr_cr, latest_fx_map


PAIRS = ["USDINR", "GBPINR", "SGDINR", "USDGBP", "USDSGD"]


def fx_pack(
    db: Session,
    reporting: str = "INR",
    scenario: str = "base",
    hedge_ratio: float = 0.5,
    hedge_style: str = "partial",
    usd_inr: float | None = None,
) -> dict:
    fx = latest_fx_map(db)
    spot = dict(fx)
    if usd_inr is not None:
        scale = usd_inr / spot.get("USDINR", usd_inr)
        spot["USDINR"] = usd_inr
        spot["GBPINR"] = spot.get("GBPINR", 106) * (0.4 + 0.6 * scale)
        spot["SGDINR"] = spot.get("SGDINR", 62) * (0.5 + 0.5 * scale)

    pos = positions_at(db, AS_OF, scenario)
    sim = simulate_strategy(pos, "none")
    # Transaction exposure ≈ FX-sensitive flows; translation ≈ non-INR cash; economic ≈ 12m stressed.
    tx = sim["totals"]["fx"]
    translation = sum(p.inr_closing for p in sim["positions"] if p.country != "IN")
    economic = tx * 1.35
    inflows_usd = sum(p.inr_inflows * 0.22 for p in sim["positions"])
    outflows_usd = sum(p.inr_outflows * 0.18 for p in sim["positions"])
    natural = net_currency_exposure(inflows_usd, outflows_usd)

    styles = {
        "unhedged": 0.0,
        "natural": 0.25,
        "forward": hedge_ratio,
        "partial": hedge_ratio,
    }
    ratio = styles.get(hedge_style, hedge_ratio)
    residual = hedge_residual(tx, ratio)
    cost = hedge_cost(tx, ratio, 28)  # 28 bps illustrative

    history = []
    rows = (
        db.query(ExchangeRate)
        .filter(ExchangeRate.pair.in_(PAIRS))
        .order_by(ExchangeRate.as_of)
        .all()
    )
    by_date: dict[str, dict] = {}
    for r in rows:
        k = r.as_of.isoformat()[:7]
        by_date.setdefault(k, {})
        by_date[k][r.pair] = r.rate
    for k in sorted(by_date):
        history.append({"period": k, **by_date[k]})

    slider_path = []
    base_usd = fx.get("USDINR", 83.4)
    cash0 = sim["totals"]["cash"]
    for rate in (75, 80, 83, 85, 90, 95):
        shock = (rate / base_usd) - 1
        cash1 = cash0 * (1 + shock * 0.42)  # share of group NAV that is FX-sensitive
        slider_path.append(
            {
                "usd_inr": rate,
                "cash": convert_inr_cr(cash1, reporting, fx),
                "delta": convert_inr_cr(cash1 - cash0, reporting, fx),
                "receivables": convert_inr_cr(tx * 0.55 * (1 + shock), reporting, fx),
                "payables": convert_inr_cr(tx * 0.40 * (1 + shock), reporting, fx),
            }
        )

    stresses = []
    for ccy, pair in [("INR", "USDINR"), ("USD", "USDINR"), ("GBP", "GBPINR"), ("SGD", "SGDINR")]:
        for pct in (-0.10, -0.05, 0.05, 0.10):
            before = sim["totals"]["cash"]
            after = before * (1 + pct * (0.42 if ccy != "INR" else -0.42))
            # INR strengthening (negative USDINR shock) reduces INR value of foreign cash.
            if ccy == "INR":
                after = before * (1 - pct * 0.42)
            stresses.append(
                {
                    "currency": ccy,
                    "shock_pct": pct,
                    "label": _shock_label(ccy, pct),
                    "before": convert_inr_cr(before, reporting, fx),
                    "after": convert_inr_cr(after, reporting, fx),
                    "change": convert_inr_cr(after - before, reporting, fx),
                    "change_pct": (after - before) / before if before else 0,
                }
            )

    return {
        "meta": reporting_meta(reporting, fx),
        "spot": spot,
        "pairs": PAIRS,
        "history": history,
        "transaction": convert_inr_cr(tx, reporting, fx),
        "translation": convert_inr_cr(translation, reporting, fx),
        "economic": convert_inr_cr(economic, reporting, fx),
        "natural_hedge": {
            "usd_inflows": convert_inr_cr(inflows_usd, reporting, fx),
            "usd_outflows": convert_inr_cr(outflows_usd, reporting, fx),
            "net": convert_inr_cr(natural, reporting, fx),
            "explain": "If USD inflows and USD outflows occur in the same period, Net Exposure = USD in − USD out. Matching flows reduces conversion need.",
        },
        "hedge": {
            "style": hedge_style,
            "ratio": ratio,
            "residual": convert_inr_cr(residual, reporting, fx),
            "cost": convert_inr_cr(cost, reporting, fx),
            "risk": convert_inr_cr(residual, reporting, fx),
            "explain": {
                "unhedged": "Full FX volatility hits reported cash and earnings.",
                "natural": "Offset exposures with opposite-direction flows in the same currency.",
                "forward": "Lock a rate with an FX forward. Illustrative only — no trade is executed.",
                "partial": "Hedge a chosen ratio. Residual risk remains on the unhedged sleeve.",
            },
        },
        "slider": slider_path,
        "stress": stresses,
        "definitions": {
            "transaction": "FX risk on committed cash flows denominated in foreign currency.",
            "translation": "FX risk on converting foreign-entity balances into the reporting currency.",
            "economic": "Longer-run competitiveness / volume impact of FX on the franchise.",
        },
        "disclaimer": "Conceptual module. No actual trades are executed.",
    }


def _shock_label(ccy: str, pct: float) -> str:
    direction = "strengthens" if pct < 0 else "weakens"
    if ccy == "INR":
        direction = "strengthens" if pct < 0 else "weakens"
    return f"{ccy} {direction} {abs(int(pct * 100))}%"
