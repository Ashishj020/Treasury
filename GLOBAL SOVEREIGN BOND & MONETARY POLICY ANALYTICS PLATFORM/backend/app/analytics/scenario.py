"""Illustrative scenario engine. Not a forecast — documented linear elasticities."""

from __future__ import annotations

# Elasticities are pedagogical: short end more policy-sensitive than long end.
# Units: bp yield response per 1 bp local policy change, plus additive shocks.
ELASTICITY = {
    "US": {"2Y": 0.85, "10Y": 0.32, "30Y": 0.18, "own": "fed_bp"},
    "IN": {"2Y": 0.72, "10Y": 0.28, "30Y": 0.16, "own": "rbi_bp"},
    "UK": {"2Y": 0.80, "10Y": 0.34, "30Y": 0.20, "own": "boe_bp"},
    "EZ": {"2Y": 0.78, "10Y": 0.30, "30Y": 0.17, "own": "ecb_bp"},
}

# Cross-market spillover from Fed policy onto other 10Y yields (bp per Fed bp).
FED_SPILLOVER_10Y = {"US": 0.0, "IN": 0.12, "UK": 0.18, "EZ": 0.16}


def run_scenario(
    fed_bp: float,
    rbi_bp: float,
    boe_bp: float,
    ecb_bp: float,
    inflation_shock_pp: float,
    growth_shock_pp: float,
    risk_off: float,
) -> dict:
    shocks = {"fed_bp": fed_bp, "rbi_bp": rbi_bp, "boe_bp": boe_bp, "ecb_bp": ecb_bp}
    out: dict[str, dict] = {}
    for mkt, e in ELASTICITY.items():
        own = shocks[str(e["own"])]
        d2 = e["2Y"] * own
        d10 = e["10Y"] * own + FED_SPILLOVER_10Y[mkt] * fed_bp
        d30 = e["30Y"] * own + 0.6 * FED_SPILLOVER_10Y[mkt] * fed_bp
        # Inflation lifts the whole curve; growth steepens; risk-off is a flight-to-quality
        # in US/EZ/UK duration and a mild cheapening of India (EM risk premium).
        inf = inflation_shock_pp * 100
        gr = growth_shock_pp * 100
        d2 += 0.15 * inf - 0.05 * gr
        d10 += 0.35 * inf + 0.10 * gr
        d30 += 0.40 * inf + 0.18 * gr
        if mkt == "IN":
            d10 += 8.0 * risk_off
            d30 += 10.0 * risk_off
        else:
            d10 -= 6.0 * risk_off
            d30 -= 8.0 * risk_off
            d2 -= 2.0 * risk_off
        slope = d10 - d2
        # Duration-based illustrative price return on a 10Y par bond, mod dur ~ 8.
        ret_10y = -8.0 * (d10 / 10000.0)
        out[mkt] = {
            "d2_bp": round(d2, 2),
            "d10_bp": round(d10, 2),
            "d30_bp": round(d30, 2),
            "slope_bp": round(slope, 2),
            "approx_10y_return_pct": round(ret_10y * 100, 3),
        }
    return {
        "disclaimer": "ILLUSTRATIVE SCENARIO — NOT A FORECAST",
        "assumptions": {
            "short_end_elasticity": "2Y moves ~70–85% of the local policy impulse",
            "long_end_elasticity": "10Y moves ~28–34% plus a documented Fed spillover",
            "duration": "10Y price return uses modified duration of 8",
            "risk_off": "Flight-to-quality in G3 duration; India risk premium widens",
        },
        "markets": out,
    }
