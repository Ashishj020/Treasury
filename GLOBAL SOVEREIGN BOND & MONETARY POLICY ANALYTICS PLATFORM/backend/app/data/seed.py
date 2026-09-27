from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.generate_demo import generate
from app.models.tables import (
    BondReturn,
    CentralBank,
    Country,
    DataSource,
    MacroIndicator,
    MarketEvent,
    PolicyEvent,
    PolicyRate,
    SovereignYield,
)

SOURCES = [
    {
        "code": "DEMO-UST",
        "name": "Simulated U.S. Treasury par yields",
        "institution": "Constructed series inspired by U.S. Treasury / FRED H.15",
        "variable": "Par yields 3M–30Y; Fed Funds upper bound",
        "frequency": "Business daily (yields, policy); monthly (macro)",
        "date_range": "2015-01-02 → 2026-09-16",
        "transformation": "Nelson-Siegel interpolation of a time-varying (β0, β1, β2) state driven by a step policy path.",
        "methodology": "Not a reprint of FRED. Shape of hiking/easing cycles is historically recognisable so students can practise event studies. Always labelled DEMO.",
        "url": "https://fred.stlouisfed.org/",
        "demo": 1,
    },
    {
        "code": "DEMO-IN",
        "name": "Simulated India G-Sec par yields",
        "institution": "Constructed series inspired by RBI / CCIL / FBIL",
        "variable": "G-Sec par yields; RBI repo rate",
        "frequency": "Business daily / monthly",
        "date_range": "2015-01-02 → 2026-09-16",
        "transformation": "Same NS engine; India has a higher level and a milder inversion than UST.",
        "methodology": "Repo waypoints follow the publicly remembered RBI cycle (COVID low at 4%, terminal 6.50%). Not official CCIL closes.",
        "url": "https://www.rbi.org.in/",
        "demo": 1,
    },
    {
        "code": "DEMO-UK",
        "name": "Simulated gilt par yields",
        "institution": "Constructed series inspired by BoE / UK DMO",
        "variable": "Gilt par yields; Bank Rate",
        "frequency": "Business daily / monthly",
        "date_range": "2015-01-02 → 2026-09-16",
        "transformation": "Includes a 12-session spike around 23 Sep 2022 to teach LDI / duration stress.",
        "methodology": "Not DMO reference prices. Use only as a laboratory dataset.",
        "url": "https://www.bankofengland.co.uk/",
        "demo": 1,
    },
    {
        "code": "DEMO-EZ",
        "name": "Simulated German Bund par yields",
        "institution": "Constructed series inspired by ECB SDW / Eurostat",
        "variable": "Bund par yields; ECB deposit facility rate",
        "frequency": "Business daily / monthly",
        "date_range": "2015-01-02 → 2026-09-16",
        "transformation": "Allows mildly negative yields in the 2015–21 window.",
        "methodology": "Eurozone 'sovereign' here means the German benchmark, not a GDP-weighted euro area composite. Stated on the Data Sources page.",
        "url": "https://data.ecb.europa.eu/",
        "demo": 1,
    },
    {
        "code": "DEMO-MACRO",
        "name": "Simulated macro drivers",
        "institution": "Inspired by BLS / BEA / ONS / Eurostat / MOSPI / EIA / CBOE",
        "variable": "CPI y/y, real GDP y/y, unemployment, FX, M2 growth, WTI, VIX",
        "frequency": "Monthly (macro); daily (VIX, oil)",
        "date_range": "2015-01 → 2026-09",
        "transformation": "AR(1) residuals around historically recognisable humps (COVID unemployment, 2022 CPI).",
        "methodology": "Do not cite as official statistics. Correlation with yields is planted by construction and by shared shocks — treat as a sandbox.",
        "url": "https://www.imf.org/",
        "demo": 1,
    },
]


def seed_if_empty(db: Session) -> None:
    if db.query(Country).count() > 0:
        return
    seed(db)


def seed(db: Session) -> None:
    payload = generate()
    countries: dict[str, Country] = {}
    banks: dict[str, CentralBank] = {}

    for code, meta in payload["markets"].items():
        c = Country(
            code=code,
            name=meta["name"],
            region=meta["region"],
            currency=meta["currency"],
            benchmark_label=meta["benchmark"],
        )
        db.add(c)
        db.flush()
        cb = CentralBank(
            country_id=c.id,
            code=meta["cb_code"],
            name=meta["cb_name"],
            policy_rate_name=meta["policy_name"],
        )
        db.add(cb)
        db.flush()
        countries[code] = c
        banks[meta["cb_code"]] = cb
        banks[code] = cb  # also index by market

    dates = payload["dates"]
    policy_rows = []
    for code, series in payload["policy"].items():
        cb = banks[code]
        policy_rows.extend(
            {"central_bank_id": cb.id, "date": d, "value": v, "source": "DEMO", "frequency": "daily"}
            for d, v in zip(dates, series)
        )
    db.bulk_insert_mappings(PolicyRate, policy_rows)

    yield_rows = []
    for code, tens in payload["yields"].items():
        c = countries[code]
        inst = payload["markets"][code]["instrument"]
        for ten, series in tens.items():
            yield_rows.extend(
                {
                    "country_id": c.id,
                    "date": d,
                    "maturity": ten,
                    "instrument": inst,
                    "value": float(v),
                    "source": "DEMO",
                    "frequency": "daily",
                }
                for d, v in zip(dates, series)
            )
    db.bulk_insert_mappings(SovereignYield, yield_rows)

    ret_rows = []
    for code, tens in payload["returns"].items():
        c = countries[code]
        for ten, recs in tens.items():
            ret_rows.extend(
                {
                    "country_id": c.id,
                    "date": r["date"],
                    "maturity": ten,
                    "price_return": r["price_return"],
                    "coupon_return": r["coupon_return"],
                    "total_return": r["total_return"],
                    "source": "DEMO",
                    "frequency": "daily",
                }
                for r in recs
            )
    db.bulk_insert_mappings(BondReturn, ret_rows)

    months = payload["months"]
    macro_rows = []
    for code, mac in payload["macro"].items():
        c = countries[code]
        for key, series in mac.items():
            macro_rows.extend(
                {
                    "country_id": c.id,
                    "date": d,
                    "indicator": key,
                    "value": float(v),
                    "source": "DEMO",
                    "frequency": "monthly",
                }
                for d, v in zip(months, series)
            )
    us = countries["US"]
    macro_rows.extend(
        {"country_id": us.id, "date": d, "indicator": "oil", "value": float(v), "source": "DEMO", "frequency": "monthly"}
        for d, v in zip(months, payload["oil_m"])
    )
    macro_rows.extend(
        {"country_id": us.id, "date": d, "indicator": "vix", "value": float(v), "source": "DEMO", "frequency": "monthly"}
        for d, v in zip(months, payload["vix_m"])
    )
    db.bulk_insert_mappings(MacroIndicator, macro_rows)

    for ev in payload["policy_events"]:
        cb = banks[ev["cb"]]
        db.add(
            PolicyEvent(
                central_bank_id=cb.id,
                date=ev["date"],
                event_type=ev["type"],
                policy_rate=ev["rate"],
                change_bp=ev["bp"],
                decision=ev["decision"],
                rationale=ev["rationale"],
                source="DEMO",
            )
        )

    for ev in payload["market_events"]:
        db.add(
            MarketEvent(
                date=ev["date"],
                code=ev["code"],
                title=ev["title"],
                category=ev["category"],
                description=ev["description"],
                markets=ev["markets"],
            )
        )

    for s in SOURCES:
        db.add(DataSource(**s))

    db.commit()
