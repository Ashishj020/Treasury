export const API = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || `Request failed ${r.status}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  health: () => req<{ demo_mode: boolean }>("/health"),
  markets: () => req<Market[]>("/markets"),
  status: () => req<Status>("/status"),
  overview: (range = "5Y", frequency = "daily") =>
    req<Overview>(`/overview?range=${range}&frequency=${frequency}`),
  series: (market: string, maturity = "10Y", range = "5Y", frequency = "daily") =>
    req<SeriesResp>(`/series?market=${market}&maturity=${maturity}&range=${range}&frequency=${frequency}`),
  curve: (market: string, asof?: string, compare = "1M,3M,1Y") =>
    req<CurveResp>(`/yield-curve?market=${market}&compare=${compare}${asof ? `&asof=${asof}` : ""}`),
  events: (cb?: string) => req<EventsResp>(`/events${cb ? `?cb=${cb}` : ""}`),
  eventStudy: (cb: string, event_type: string, window: number, market?: string, maturity = "10Y") =>
    req<EventStudy>(
      `/event-study?cb=${cb}&event_type=${event_type}&window=${window}&maturity=${maturity}${market ? `&market=${market}` : ""}`,
    ),
  returns: (maturity = "10Y", range = "MAX") => req<ReturnsResp>(`/returns?maturity=${maturity}&range=${range}`),
  risk: (market: string, window = 60, maturity = "10Y") =>
    req<RiskResp>(`/risk?market=${market}&window=${window}&maturity=${maturity}`),
  corr: (window = "1Y", kind = "yield") => req<CorrResp>(`/correlation?window=${window}&kind=${kind}`),
  scatter: (x: string, y: string) => req<ScatterResp>(`/scatter?x=${encodeURIComponent(x)}&y=${encodeURIComponent(y)}`),
  regression: (body: object) => req<RegResp>("/regression", { method: "POST", body: JSON.stringify(body) }),
  lags: (a = "IN:10Y", b = "US:10Y") => req<LagResp>(`/lags?a=${a}&b=${b}`),
  macro: (market: string) => req<MacroResp>(`/macro?market=${market}`),
  scenario: (body: object) => req<ScenarioResp>("/scenario", { method: "POST", body: JSON.stringify(body) }),
  bondLab: (body: object) => req<BondLabResp>("/bond-lab", { method: "POST", body: JSON.stringify(body) }),
  comparison: (range = "5Y") => req<CompResp>(`/comparison?range=${range}`),
  regimes: (market: string) => req<RegimeResp>(`/regimes?market=${market}`),
  methodology: () => req<Record<string, string>>("/methodology"),
  sources: () => req<Source[]>("/sources"),
  guess: () => req<GuessResp>("/guess-curve"),
};

export type Market = {
  code: string;
  name: string;
  region: string;
  currency: string;
  central_bank: string;
  central_bank_code: string;
  policy_rate_name: string;
  benchmark_label: string;
};

export type Status = {
  demo_mode: boolean;
  label: string;
  disclaimer: string;
  last_updated: string;
  items: { market: string; status: string; observations: number; last_updated: string; demo: boolean; source: string }[];
};

export type Overview = {
  asof: string;
  kpis: { market: string; label: string; current: number; change_1d_bp: number | null; change_1m_bp: number | null; change_1y_bp: number | null; sparkline: number[] }[];
  policy: { market: string; current: number; change_90d_bp: number; sparkline: number[] }[];
  heatmap: { market: string; regime: string; cycle: string; hiking: boolean; cutting: boolean; holding: boolean; qe: boolean; qt: boolean; policy_rate: number; slope_2s10s: number | null }[];
  mood: { code: string; tone: string };
  insights: { title: string; body: string; a?: number; b?: number }[];
};

export type SeriesResp = {
  market: string;
  points: { date: string; policy: number | null; yield: number | null; y2: number | null; y10: number | null; y30: number | null; spread_2s10s: number | null }[];
  events: { date: string; code: string; title: string; category: string; description: string; markets: string }[];
  disclaimer: string;
};

export type CurveResp = {
  market: string;
  asof: string;
  points: { maturity: string; tenor_years: number; yield_pct: number }[];
  shape: string;
  personality: string;
  spread_2s10s: number;
  spread_5s30s: number | null;
  spread_10s30s: number | null;
  overlays: { label: string; asof: string; points: { maturity: string; tenor_years: number; yield_pct: number }[] }[];
};

export type EventsResp = {
  policy: {
    id: number;
    date: string;
    cb: string;
    market: string;
    event_type: string;
    policy_rate: number;
    change_bp: number;
    decision: string;
    rationale: string;
    before: Record<string, number | null>;
    event: Record<string, number | null>;
    after: Record<string, number | null>;
  }[];
  market: { date: string; code: string; title: string; category: string; description: string; markets: string }[];
};

export type EventStudy = {
  ok: boolean;
  error?: string;
  n: number;
  points?: { day: number; mean_bp: number; median_bp: number; p25_bp: number; p75_bp: number }[];
  avg_terminal_bp?: number;
  median_terminal_bp?: number;
  max_increase_bp?: number;
  max_decrease_bp?: number;
  vol_pre_bp?: number;
  vol_post_bp?: number;
  methodology?: string;
  events_used?: string[];
};

export type ReturnsResp = {
  series: Record<string, { date: string; cumulative: number; drawdown: number; total_return: number }[]>;
  stats: Record<string, { ann_return: number; ann_vol: number; max_drawdown: number; sharpe: number | null; last_12m: number | null }>;
  benchmarks: Record<string, string>;
  disclaimer: string;
};

export type RiskResp = {
  yield_vol: { date: string; value: number }[];
  return_vol: { date: string; value: number }[];
  drawdown: { date: string; value: number }[];
  var_5pct_daily: number | null;
  sharpe: number | null;
  max_drawdown: number;
  note: string;
};

export type CorrResp = {
  labels: string[];
  matrix: (number | null)[][];
  n: number;
  rolling_us_in: { date: string; value: number }[];
  note: string;
};

export type ScatterResp = {
  n: number;
  correlation: number;
  r_squared: number;
  slope: number;
  intercept: number;
  points: { x: number; y: number; date: string }[];
};

export type RegResp = {
  n: number;
  r_squared: number;
  adj_r_squared: number;
  terms: { variable: string; coefficient: number; std_error: number; t_stat: number; p_value: number }[];
  warnings: string[];
};

export type LagResp = {
  lags: { lag: number; correlation: number | null }[];
  strongest: { lag: number; correlation: number | null };
  label: string;
  interpretation: string;
};

export type MacroResp = { market: string; series: Record<string, { date: string; value: number }[]> };

export type ScenarioResp = {
  disclaimer: string;
  assumptions: Record<string, string>;
  markets: Record<string, { d2_bp: number; d10_bp: number; d30_bp: number; slope_bp: number; approx_10y_return_pct: number }>;
};

export type BondLabResp = {
  price: number;
  current_yield: number;
  macaulay: number;
  modified: number;
  convexity: number;
  actual_price: number;
  duration_approx: number;
  convexity_approx: number;
  duration_error: number;
  convexity_error: number;
  curve: { yield: number; price: number }[];
  note: string;
};

export type CompResp = {
  matrix: Record<string, Record<string, number | string | null>>;
  series: Record<string, Record<string, { date: string; value: number }[]>>;
};

export type RegimeResp = {
  rule: string;
  regimes: { regime: string; n: number; avg_2y: number; avg_10y: number; avg_vol: number; avg_return_ann: number }[];
};

export type Source = {
  code: string;
  name: string;
  institution: string;
  variable: string;
  frequency: string;
  date_range: string;
  transformation: string;
  methodology: string;
  url: string;
  demo: boolean;
};

export type GuessResp = {
  market: string;
  question: string;
  before_date: string;
  after_date: string;
  before: { maturity: string; tenor_years: number; yield_pct: number }[];
  after: { maturity: string; tenor_years: number; yield_pct: number }[];
};
