from datetime import date

from pydantic import BaseModel, Field


class MarketMeta(BaseModel):
    code: str
    name: str
    region: str
    currency: str
    central_bank: str
    central_bank_code: str
    policy_rate_name: str
    benchmark_label: str


class SeriesPoint(BaseModel):
    date: date
    value: float


class YieldPoint(BaseModel):
    date: date
    maturity: str
    value: float


class KpiCard(BaseModel):
    market: str
    label: str
    current: float
    change_1d_bp: float | None = None
    change_1m_bp: float | None = None
    change_1y_bp: float | None = None
    sparkline: list[float] = Field(default_factory=list)


class PolicyHeatCell(BaseModel):
    market: str
    regime: str
    hiking: bool
    cutting: bool
    holding: bool
    qe: bool
    qt: bool
    policy_rate: float
    slope_2s10s: float | None = None


class CurvePoint(BaseModel):
    maturity: str
    tenor_years: float
    yield_pct: float


class CurveSnapshot(BaseModel):
    market: str
    asof: date
    points: list[CurvePoint]
    shape: str
    personality: str
    spread_2s10s: float
    spread_5s30s: float
    spread_10s30s: float


class EventStudyPoint(BaseModel):
    day: int
    mean_bp: float
    median_bp: float
    p25_bp: float
    p75_bp: float
    n: int


class RegressionTerm(BaseModel):
    variable: str
    coefficient: float
    std_error: float
    t_stat: float
    p_value: float


class RegressionResult(BaseModel):
    dependent: str
    n: int
    r_squared: float
    adj_r_squared: float
    terms: list[RegressionTerm]
    warnings: list[str]


class ScenarioRequest(BaseModel):
    fed_bp: float = 0
    rbi_bp: float = 0
    boe_bp: float = 0
    ecb_bp: float = 0
    inflation_shock_pp: float = 0
    growth_shock_pp: float = 0
    risk_off: float = 0


class BondLabRequest(BaseModel):
    face: float = 100
    coupon_rate: float = 0.04
    maturity_years: float = 10
    yield_rate: float = 0.042
    frequency: int = 2
    yield_shock_bp: float = 0


class DataStatusItem(BaseModel):
    market: str
    source: str
    status: str
    last_updated: date | None
    observations: int
    frequency: str
    missing: int
    demo: bool
