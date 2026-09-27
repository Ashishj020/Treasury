"""
Historically *inspired* synthetic sovereign-rate paths for DEMO MODE.

This is NOT official FRED / RBI / BoE / ECB data. Paths follow the broad
shape of 2015–2026 policy cycles (COVID collapse, 2022 hiking inversion,
2024–26 easing) so charts teach transmission rather than reprint a vendor feed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from app.analytics.bond import nelson_siegel, total_return_from_yields

START = date(2015, 1, 2)
END = date(2026, 9, 16)
RNG = np.random.default_rng(42)

MARKETS = {
    "US": {
        "name": "United States",
        "region": "North America",
        "currency": "USD",
        "cb_code": "FED",
        "cb_name": "Federal Reserve",
        "policy_name": "Fed Funds Rate (upper)",
        "benchmark": "U.S. Treasury par curve (simulated)",
        "instrument": "UST",
    },
    "IN": {
        "name": "India",
        "region": "South Asia",
        "currency": "INR",
        "cb_code": "RBI",
        "cb_name": "Reserve Bank of India",
        "policy_name": "RBI Repo Rate",
        "benchmark": "G-Sec par curve (simulated)",
        "instrument": "IN-GSEC",
    },
    "UK": {
        "name": "United Kingdom",
        "region": "Europe",
        "currency": "GBP",
        "cb_code": "BOE",
        "cb_name": "Bank of England",
        "policy_name": "Bank Rate",
        "benchmark": "Gilt par curve (simulated)",
        "instrument": "UKT",
    },
    "EZ": {
        "name": "Eurozone",
        "region": "Europe",
        "currency": "EUR",
        "cb_code": "ECB",
        "cb_name": "European Central Bank",
        "policy_name": "Deposit Facility Rate",
        "benchmark": "German Bund par curve (simulated)",
        "instrument": "DBR",
    },
}

MATURITIES: list[tuple[str, float]] = [
    ("3M", 0.25),
    ("6M", 0.50),
    ("1Y", 1.0),
    ("2Y", 2.0),
    ("5Y", 5.0),
    ("10Y", 10.0),
    ("20Y", 20.0),
    ("30Y", 30.0),
]


def _step(dates: list[date], steps: list[tuple[date, float]]) -> np.ndarray:
    steps = sorted(steps, key=lambda x: x[0])
    out = np.zeros(len(dates))
    j = 0
    level = steps[0][1]
    for i, d in enumerate(dates):
        while j + 1 < len(steps) and d >= steps[j + 1][0]:
            j += 1
            level = steps[j][1]
        out[i] = level
    return out


def _policy_steps() -> dict[str, list[tuple[date, float]]]:
    """Coarse, publicly remembered policy waypoints — not a complete minutes archive."""
    return {
        "US": [
            (date(2015, 1, 1), 0.25),
            (date(2015, 12, 17), 0.50),
            (date(2016, 12, 15), 0.75),
            (date(2017, 3, 16), 1.00),
            (date(2017, 6, 15), 1.25),
            (date(2017, 12, 14), 1.50),
            (date(2018, 3, 22), 1.75),
            (date(2018, 6, 14), 2.00),
            (date(2018, 9, 27), 2.25),
            (date(2018, 12, 20), 2.50),
            (date(2019, 8, 1), 2.25),
            (date(2019, 9, 19), 2.00),
            (date(2019, 10, 31), 1.75),
            (date(2020, 3, 3), 1.25),
            (date(2020, 3, 16), 0.25),
            (date(2022, 3, 17), 0.50),
            (date(2022, 5, 5), 1.00),
            (date(2022, 6, 16), 1.75),
            (date(2022, 7, 28), 2.50),
            (date(2022, 9, 22), 3.25),
            (date(2022, 11, 3), 4.00),
            (date(2022, 12, 15), 4.50),
            (date(2023, 2, 2), 4.75),
            (date(2023, 3, 23), 5.00),
            (date(2023, 5, 4), 5.25),
            (date(2023, 7, 27), 5.50),
            (date(2024, 9, 18), 5.00),
            (date(2024, 11, 8), 4.75),
            (date(2024, 12, 19), 4.50),
            (date(2025, 9, 18), 4.25),
            (date(2025, 12, 11), 3.75),
            (date(2026, 3, 19), 3.75),
            (date(2026, 6, 18), 3.50),
        ],
        "IN": [
            (date(2015, 1, 1), 7.75),
            (date(2015, 3, 4), 7.50),
            (date(2016, 4, 5), 6.50),
            (date(2016, 10, 4), 6.25),
            (date(2017, 8, 2), 6.00),
            (date(2018, 6, 6), 6.25),
            (date(2018, 8, 1), 6.50),
            (date(2019, 2, 7), 6.25),
            (date(2019, 4, 4), 6.00),
            (date(2019, 6, 6), 5.75),
            (date(2019, 8, 7), 5.40),
            (date(2019, 10, 4), 5.15),
            (date(2020, 3, 27), 4.40),
            (date(2020, 5, 22), 4.00),
            (date(2022, 5, 4), 4.40),
            (date(2022, 6, 8), 4.90),
            (date(2022, 8, 5), 5.40),
            (date(2022, 9, 30), 5.90),
            (date(2022, 12, 7), 6.25),
            (date(2023, 2, 8), 6.50),
            (date(2025, 2, 7), 6.25),
            (date(2025, 6, 6), 5.50),
            (date(2025, 12, 5), 5.25),
            (date(2026, 4, 9), 5.25),
        ],
        "UK": [
            (date(2015, 1, 1), 0.50),
            (date(2016, 8, 4), 0.25),
            (date(2017, 11, 2), 0.50),
            (date(2018, 8, 2), 0.75),
            (date(2020, 3, 11), 0.25),
            (date(2020, 3, 19), 0.10),
            (date(2021, 12, 16), 0.25),
            (date(2022, 2, 3), 0.50),
            (date(2022, 3, 17), 0.75),
            (date(2022, 5, 5), 1.00),
            (date(2022, 6, 16), 1.25),
            (date(2022, 8, 4), 1.75),
            (date(2022, 9, 22), 2.25),
            (date(2022, 11, 3), 3.00),
            (date(2022, 12, 15), 3.50),
            (date(2023, 2, 2), 4.00),
            (date(2023, 3, 23), 4.25),
            (date(2023, 5, 11), 4.50),
            (date(2023, 6, 22), 5.00),
            (date(2023, 8, 3), 5.25),
            (date(2024, 8, 1), 5.00),
            (date(2024, 11, 7), 4.75),
            (date(2025, 2, 6), 4.50),
            (date(2025, 5, 8), 4.25),
            (date(2025, 8, 7), 4.00),
            (date(2025, 11, 6), 4.00),
            (date(2026, 5, 7), 3.75),
        ],
        "EZ": [
            (date(2015, 1, 1), -0.20),
            (date(2015, 12, 9), -0.30),
            (date(2016, 3, 16), -0.40),
            (date(2019, 9, 18), -0.50),
            (date(2022, 7, 27), 0.00),
            (date(2022, 9, 14), 0.75),
            (date(2022, 11, 2), 1.50),
            (date(2022, 12, 21), 2.00),
            (date(2023, 2, 8), 2.50),
            (date(2023, 3, 22), 3.00),
            (date(2023, 5, 10), 3.25),
            (date(2023, 6, 21), 3.50),
            (date(2023, 7, 27), 3.75),
            (date(2023, 9, 14), 4.00),
            (date(2024, 6, 12), 3.75),
            (date(2024, 9, 18), 3.50),
            (date(2024, 10, 23), 3.25),
            (date(2024, 12, 12), 3.00),
            (date(2025, 3, 6), 2.50),
            (date(2025, 4, 17), 2.25),
            (date(2025, 6, 5), 2.00),
            (date(2026, 3, 12), 2.00),
            (date(2026, 6, 11), 1.75),
        ],
    }


def _qe_windows() -> dict[str, list[tuple[date, date]]]:
    return {
        "US": [(date(2020, 3, 15), date(2022, 3, 1))],
        "IN": [(date(2020, 3, 27), date(2021, 10, 1))],
        "UK": [(date(2020, 3, 19), date(2021, 12, 16))],
        "EZ": [(date(2015, 3, 9), date(2018, 12, 1)), (date(2020, 3, 18), date(2022, 6, 1))],
    }


def _qt_windows() -> dict[str, list[tuple[date, date]]]:
    return {
        "US": [(date(2017, 10, 1), date(2019, 8, 1)), (date(2022, 6, 1), date(2024, 6, 1))],
        "IN": [],
        "UK": [(date(2022, 11, 1), date(2025, 6, 1))],
        "EZ": [(date(2023, 3, 1), date(2025, 6, 1))],
    }


def _in_window(d: date, windows: list[tuple[date, date]]) -> bool:
    return any(a <= d <= b for a, b in windows)


POLICY_EVENTS: list[dict[str, Any]] = [
    {"cb": "FED", "date": date(2015, 12, 17), "type": "HIKE", "rate": 0.50, "bp": 25, "decision": "RATE HIKE", "rationale": "Lift-off after seven years at the zero lower bound; labour market tightening."},
    {"cb": "FED", "date": date(2018, 12, 20), "type": "HIKE", "rate": 2.50, "bp": 25, "decision": "RATE HIKE", "rationale": "Final hike of the 2015–18 cycle; later seen as one hike too many by some FOMC members."},
    {"cb": "FED", "date": date(2020, 3, 16), "type": "CUT", "rate": 0.25, "bp": -100, "decision": "EMERGENCY CUT", "rationale": "COVID emergency: funds rate back to the effective lower bound."},
    {"cb": "FED", "date": date(2020, 3, 23), "type": "QE", "rate": 0.25, "bp": 0, "decision": "QE ANNOUNCEMENT", "rationale": "Unlimited Treasury and MBS purchases; credit facilities."},
    {"cb": "FED", "date": date(2022, 3, 17), "type": "HIKE", "rate": 0.50, "bp": 25, "decision": "RATE HIKE", "rationale": "Start of the inflation-fighting cycle."},
    {"cb": "FED", "date": date(2022, 6, 16), "type": "HIKE", "rate": 1.75, "bp": 75, "decision": "RATE HIKE", "rationale": "75 bp hike after CPI surprise; most aggressive since 1994."},
    {"cb": "FED", "date": date(2022, 6, 1), "type": "QT", "rate": 0.75, "bp": 0, "decision": "QT ANNOUNCEMENT", "rationale": "Balance-sheet runoff begins; quantitative tightening."},
    {"cb": "FED", "date": date(2023, 3, 23), "type": "HIKE", "rate": 5.00, "bp": 25, "decision": "RATE HIKE", "rationale": "Hike through SVB stress; 'higher for longer' language."},
    {"cb": "FED", "date": date(2023, 7, 27), "type": "HOLD", "rate": 5.50, "bp": 25, "decision": "RATE HIKE", "rationale": "Terminal hike of the cycle to 5.25–5.50%."},
    {"cb": "FED", "date": date(2024, 9, 18), "type": "CUT", "rate": 5.00, "bp": -50, "decision": "RATE CUT", "rationale": "First cut of the easing cycle; 50 bp as inflation cooled."},
    {"cb": "FED", "date": date(2025, 12, 11), "type": "CUT", "rate": 3.75, "bp": -25, "decision": "RATE CUT", "rationale": "Continued normalisation toward estimated r*."},
    {"cb": "RBI", "date": date(2020, 3, 27), "type": "CUT", "rate": 4.40, "bp": -75, "decision": "EMERGENCY CUT", "rationale": "COVID off-cycle cut; liquidity measures."},
    {"cb": "RBI", "date": date(2020, 5, 22), "type": "CUT", "rate": 4.00, "bp": -40, "decision": "RATE CUT", "rationale": "Repo taken to the cycle low."},
    {"cb": "RBI", "date": date(2022, 5, 4), "type": "HIKE", "rate": 4.40, "bp": 40, "decision": "RATE HIKE", "rationale": "Off-cycle start of the hiking cycle as CPI printed above target."},
    {"cb": "RBI", "date": date(2023, 2, 8), "type": "HIKE", "rate": 6.50, "bp": 25, "decision": "RATE HIKE", "rationale": "Terminal hike; pause thereafter."},
    {"cb": "RBI", "date": date(2025, 2, 7), "type": "CUT", "rate": 6.25, "bp": -25, "decision": "RATE CUT", "rationale": "Start of a cautious easing cycle."},
    {"cb": "BOE", "date": date(2016, 8, 4), "type": "CUT", "rate": 0.25, "bp": -25, "decision": "RATE CUT", "rationale": "Post-referendum easing plus gilt QE."},
    {"cb": "BOE", "date": date(2020, 3, 19), "type": "CUT", "rate": 0.10, "bp": -15, "decision": "EMERGENCY CUT", "rationale": "COVID Bank Rate to 0.10%; APF expanded."},
    {"cb": "BOE", "date": date(2021, 12, 16), "type": "HIKE", "rate": 0.25, "bp": 15, "decision": "RATE HIKE", "rationale": "First G7 hike of the inflation cycle."},
    {"cb": "BOE", "date": date(2022, 9, 23), "type": "STRESS", "rate": 2.25, "bp": 0, "decision": "MARKET STRESS", "rationale": "Mini-budget gilt crisis; BoE temporary gilt purchases."},
    {"cb": "BOE", "date": date(2023, 8, 3), "type": "HIKE", "rate": 5.25, "bp": 25, "decision": "RATE HIKE", "rationale": "Terminal Bank Rate of the cycle."},
    {"cb": "BOE", "date": date(2024, 8, 1), "type": "CUT", "rate": 5.00, "bp": -25, "decision": "RATE CUT", "rationale": "First cut as services inflation cooled."},
    {"cb": "ECB", "date": date(2015, 3, 9), "type": "QE", "rate": -0.20, "bp": 0, "decision": "QE ANNOUNCEMENT", "rationale": "PSPP launch — public-sector purchase programme."},
    {"cb": "ECB", "date": date(2019, 9, 18), "type": "CUT", "rate": -0.50, "bp": -10, "decision": "RATE CUT", "rationale": "Deposit rate to −0.50%; QE restarted."},
    {"cb": "ECB", "date": date(2022, 7, 27), "type": "HIKE", "rate": 0.00, "bp": 50, "decision": "RATE HIKE", "rationale": "Exit from negative rates; TPI announced."},
    {"cb": "ECB", "date": date(2023, 9, 14), "type": "HIKE", "rate": 4.00, "bp": 25, "decision": "RATE HIKE", "rationale": "Terminal deposit rate."},
    {"cb": "ECB", "date": date(2024, 6, 12), "type": "CUT", "rate": 3.75, "bp": -25, "decision": "RATE CUT", "rationale": "First cut of the easing cycle, ahead of the Fed."},
]

MARKET_EVENTS = [
    {"code": "COVID", "date": date(2020, 3, 16), "title": "COVID policy shock", "category": "COVID", "description": "Global emergency easing. Policy rates collapsed to the effective lower bound; QE restarted; curves bull-steepened then flattened as the recovery priced in.", "markets": "US,IN,UK,EZ"},
    {"code": "INFLATION", "date": date(2021, 11, 10), "title": "Inflation shock", "category": "INFLATION SHOCK", "description": "CPI prints made 'transitory' untenable. Term premia and short-rate expectations both rose; 2022 delivered the fastest hiking cycle in a generation.", "markets": "US,IN,UK,EZ"},
    {"code": "HIKING_START", "date": date(2022, 3, 17), "title": "Global hiking cycle", "category": "RATE HIKE", "description": "Fed lift-off from the ELB. Short-end yields led; curves flattened then inverted as markets priced a hard landing that mostly did not arrive.", "markets": "US,UK,EZ"},
    {"code": "GILT_CRISIS", "date": date(2022, 9, 23), "title": "UK gilt / LDI stress", "category": "BANKING STRESS", "description": "Unfunded fiscal announcement met leveraged liability-driven investors. 30Y gilt yields spiked; BoE bought long gilts as a financial-stability operation.", "markets": "UK"},
    {"code": "SVB", "date": date(2023, 3, 10), "title": "Banking stress (SVB)", "category": "BANKING STRESS", "description": "Duration losses on HTM books crystallised. Flight-to-quality rally in Treasuries; Fed hiked anyway two weeks later.", "markets": "US"},
    {"code": "QT", "date": date(2022, 6, 1), "title": "Quantitative tightening", "category": "QT", "description": "Balance-sheet runoff. The term-premium channel is the one that is least identified — treat QT markers as regime labels, not isolated shocks.", "markets": "US,UK,EZ"},
    {"code": "EASING", "date": date(2024, 9, 18), "title": "Easing cycle begins", "category": "RATE CUT", "description": "Fed 50 bp cut. Curves bull-steepened as the short end led lower. Long-end moves were smaller and more about term premium and fiscal supply.", "markets": "US,UK,EZ,IN"},
    {"code": "RECESSION_SCARE", "date": date(2022, 7, 1), "title": "Soft-landing debate", "category": "RECESSION", "description": "Deep inversion of 2s10s. This lab treats inversion as a slope observation, not a recession call.", "markets": "US,UK,EZ"},
]


def _smooth_ar1(n: int, sigma: float, phi: float = 0.97) -> np.ndarray:
    e = RNG.normal(0, sigma, n)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def generate() -> dict[str, Any]:
    bdays = pd.bdate_range(START, END)
    dates = [d.date() for d in bdays]
    n = len(dates)
    t = np.arange(n) / 252.0
    steps = _policy_steps()
    qe = _qe_windows()
    qt = _qt_windows()

    policy: dict[str, np.ndarray] = {}
    for mkt, st in steps.items():
        policy[mkt] = _step(dates, st)

    # Shared global factors
    vix = 14 + 6 * np.sin(2 * np.pi * t / 4.2) + _smooth_ar1(n, 0.35)
    vix = np.clip(vix, 9, None)
    covid_idx = dates.index(min(dates, key=lambda d: abs((d - date(2020, 3, 16)).days)))
    inf_idx = dates.index(min(dates, key=lambda d: abs((d - date(2022, 3, 1)).days)))
    svb_idx = dates.index(min(dates, key=lambda d: abs((d - date(2023, 3, 10)).days)))
    gilt_idx = dates.index(min(dates, key=lambda d: abs((d - date(2022, 9, 23)).days)))
    vix[covid_idx : covid_idx + 40] += np.linspace(45, 4, 40)
    vix[inf_idx : inf_idx + 80] += np.linspace(8, 0, 80)
    vix[svb_idx : svb_idx + 15] += np.linspace(18, 0, 15)
    oil = 55 + 25 * np.sin(2 * np.pi * (t - 0.4) / 5) + _smooth_ar1(n, 0.8)
    oil = np.clip(oil, 18, None)
    oil[covid_idx : covid_idx + 30] -= np.linspace(35, 0, 30)
    oil[inf_idx - 40 : inf_idx + 60] += np.linspace(10, 40, 100)[:100] if inf_idx > 40 else 20

    ns: dict[str, dict[str, np.ndarray]] = {}
    for mkt, pol in policy.items():
        qe_flag = np.array([1.0 if _in_window(d, qe[mkt]) else 0.0 for d in dates])
        qt_flag = np.array([1.0 if _in_window(d, qt[mkt]) else 0.0 for d in dates])
        # Expected future short rate: sluggish policy + hiking-cycle overshoot.
        dpol = np.diff(pol, prepend=pol[0])
        hike_cycle = pd.Series(dpol).rolling(60, min_periods=1).sum().to_numpy()
        # Level (long rate)
        if mkt == "US":
            b0 = 2.3 + 0.55 * pol + 0.04 * (oil - 70) / 10 + _smooth_ar1(n, 0.025)
            b0[covid_idx : covid_idx + 90] -= np.linspace(0.9, 0.15, 90)
            b0[inf_idx : inf_idx + 200] += np.linspace(0.2, 1.1, 200)
        elif mkt == "IN":
            b0 = 6.4 + 0.45 * (pol - 6) + 0.08 * (vix - 16) / 10 + _smooth_ar1(n, 0.03)
        elif mkt == "UK":
            b0 = 1.8 + 0.50 * pol + 0.03 * (oil - 70) / 10 + _smooth_ar1(n, 0.028)
            b0[gilt_idx : gilt_idx + 12] += np.linspace(0.9, 0.05, 12)
        else:
            b0 = 0.9 + 0.55 * np.maximum(pol, 0) + 0.25 * pol + _smooth_ar1(n, 0.022)
            b0 = np.clip(b0, -0.6, None)

        # Slope: b1 ≈ short − long. Hiking → less negative / positive (inversion).
        b1 = (pol - b0) * 0.85 - 0.15 * qe_flag + 0.10 * qt_flag
        b1 += 0.35 * np.clip(hike_cycle, 0, None) - 0.25 * np.clip(-hike_cycle, 0, None)
        b1 += _smooth_ar1(n, 0.02)
        if mkt == "US":
            # Classic 2022–23 inversion
            b1[inf_idx + 80 : inf_idx + 420] += 0.55

        b2 = 0.4 - 0.6 * qe_flag + 0.3 * qt_flag + _smooth_ar1(n, 0.03)
        ns[mkt] = {"b0": b0, "b1": b1, "b2": b2, "qe": qe_flag, "qt": qt_flag}

    yields: dict[str, dict[str, np.ndarray]] = {m: {} for m in MARKETS}
    for mkt in MARKETS:
        for label, tau in MATURITIES:
            y = np.array([nelson_siegel(tau, ns[mkt]["b0"][i], ns[mkt]["b1"][i], ns[mkt]["b2"][i]) for i in range(n)])
            y += _smooth_ar1(n, 0.008 + 0.002 * tau)
            if mkt == "EZ":
                y = np.clip(y, -0.9, None)
            else:
                y = np.clip(y, 0.01, None)
            yields[mkt][label] = y

    # Macro — monthly
    months = pd.date_range(START, END, freq="ME")
    mdates = [d.date() for d in months]
    macro: dict[str, dict[str, list]] = {}
    for mkt, pol in policy.items():
        pol_m = np.interp(pd.DatetimeIndex(months).asi8, pd.DatetimeIndex(bdays).asi8, pol)
        if mkt == "US":
            inf = 1.7 + 0.15 * pol_m + _smooth_ar1(len(months), 0.08, 0.92)
            inf = inf.copy()
            # 2021-23 inflation hump
            for i, d in enumerate(mdates):
                if date(2021, 1, 1) <= d <= date(2023, 6, 1):
                    inf[i] += 3.8 * np.sin(np.pi * (d - date(2021, 1, 1)).days / (2 * 365))
            gdp = 2.1 - 0.15 * (pol_m - 2) + _smooth_ar1(len(months), 0.12, 0.85)
            u = 4.8 - 0.25 * (pol_m - 1) + _smooth_ar1(len(months), 0.05, 0.94)
            u = np.clip(u, 3.2, 15)
            for i, d in enumerate(mdates):
                if date(2020, 4, 1) <= d <= date(2020, 8, 1):
                    u[i] += 8
                    gdp[i] -= 8
                    inf[i] -= 1.2
            fx = np.ones(len(months))  # DXY-ish index later
            m2 = 6 + 4 * np.array([1.0 if _in_window(d, qe[mkt]) else 0.0 for d in mdates]) + _smooth_ar1(len(months), 0.2, 0.9)
        elif mkt == "IN":
            inf = 4.8 + 0.2 * (pol_m - 6) + _smooth_ar1(len(months), 0.1, 0.9)
            gdp = 6.5 - 0.2 * (pol_m - 6) + _smooth_ar1(len(months), 0.15, 0.85)
            u = 7.2 + _smooth_ar1(len(months), 0.06, 0.93)
            fx = 66 + np.linspace(0, 18, len(months)) + _smooth_ar1(len(months), 0.15, 0.95)  # USDINR
            m2 = 10 + _smooth_ar1(len(months), 0.2, 0.9)
            for i, d in enumerate(mdates):
                if date(2020, 4, 1) <= d <= date(2020, 9, 1):
                    gdp[i] -= 12
        elif mkt == "UK":
            inf = 1.8 + 0.2 * pol_m + _smooth_ar1(len(months), 0.09, 0.9)
            for i, d in enumerate(mdates):
                if date(2021, 6, 1) <= d <= date(2023, 12, 1):
                    inf[i] += 5.5 * np.sin(np.pi * (d - date(2021, 6, 1)).days / (800))
            gdp = 1.6 - 0.2 * pol_m + _smooth_ar1(len(months), 0.12, 0.85)
            u = 4.3 + _smooth_ar1(len(months), 0.05, 0.94)
            fx = 1.32 - np.linspace(0, 0.08, len(months)) + _smooth_ar1(len(months), 0.004, 0.94)  # GBPUSD
            m2 = 5 + _smooth_ar1(len(months), 0.18, 0.9)
        else:
            inf = 1.2 + 0.18 * np.maximum(pol_m, 0) + _smooth_ar1(len(months), 0.07, 0.9)
            for i, d in enumerate(mdates):
                if date(2021, 6, 1) <= d <= date(2023, 10, 1):
                    inf[i] += 4.2 * np.sin(np.pi * (d - date(2021, 6, 1)).days / (750))
            gdp = 1.4 - 0.15 * np.maximum(pol_m, 0) + _smooth_ar1(len(months), 0.1, 0.85)
            u = 8.2 - np.linspace(0, 1.6, len(months)) + _smooth_ar1(len(months), 0.04, 0.95)
            fx = 1.12 + _smooth_ar1(len(months), 0.004, 0.94)  # EURUSD
            m2 = 4.5 + _smooth_ar1(len(months), 0.16, 0.9)
        macro[mkt] = {
            "inflation": list(np.round(inf, 3)),
            "gdp": list(np.round(gdp, 3)),
            "unemployment": list(np.round(np.clip(u, 2.5, 20), 3)),
            "fx": list(np.round(fx, 4)),
            "m2": list(np.round(m2, 3)),
        }

    # Constant-maturity total returns
    returns: dict[str, dict[str, list[dict]]] = {}
    for mkt in MARKETS:
        returns[mkt] = {}
        for tenor in ("2Y", "10Y", "30Y"):
            y = yields[mkt][tenor]
            years = {"2Y": 2.0, "10Y": 10.0, "30Y": 30.0}[tenor]
            rows = []
            for i in range(1, n):
                tr = total_return_from_yields(float(y[i - 1] / 100), float(y[i] / 100), float(y[i - 1] / 100), years)
                rows.append(
                    {
                        "date": dates[i],
                        "price_return": tr["price_return"],
                        "coupon_return": tr["coupon_return"],
                        "total_return": tr["total_return"],
                    }
                )
            returns[mkt][tenor] = rows

    oil_m = np.interp(pd.DatetimeIndex(months).asi8, pd.DatetimeIndex(bdays).asi8, oil)
    vix_m = np.interp(pd.DatetimeIndex(months).asi8, pd.DatetimeIndex(bdays).asi8, vix)

    return {
        "dates": dates,
        "months": mdates,
        "markets": MARKETS,
        "policy": {k: list(np.round(v, 4)) for k, v in policy.items()},
        "yields": {m: {ten: list(np.round(arr, 4)) for ten, arr in tens.items()} for m, tens in yields.items()},
        "returns": returns,
        "macro": macro,
        "vix": list(np.round(vix, 3)),
        "oil": list(np.round(oil, 3)),
        "oil_m": list(np.round(oil_m, 3)),
        "vix_m": list(np.round(vix_m, 3)),
        "qe": {m: [bool(_in_window(d, qe[m])) for d in dates] for m in MARKETS},
        "qt": {m: [bool(_in_window(d, qt[m])) for d in dates] for m in MARKETS},
        "policy_events": POLICY_EVENTS,
        "market_events": MARKET_EVENTS,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "disclaimer": "SIMULATED DATA — FOR ANALYTICAL DEMONSTRATION",
    }
