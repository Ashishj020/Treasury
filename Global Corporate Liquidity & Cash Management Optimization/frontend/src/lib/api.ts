import { qs, type Reporting, type Scenario, type Strategy } from "./format";

const base = "";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(base + path);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(base + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

export type Filters = {
  reporting: Reporting;
  scenario: Scenario;
  strategy: Strategy;
  country: string;
};

export const api = {
  overview: (f: Filters) =>
    get(`/api/overview?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy, country: f.country })}`),
  cashFlows: (f: Filters, extra: Record<string, string> = {}) =>
    get(`/api/cash-flows?${qs({ reporting: f.reporting, scenario: f.scenario, country: f.country === "ALL" ? undefined : f.country, ...extra })}`),
  liquidity: (f: Filters) =>
    get(`/api/liquidity?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy, country: f.country === "ALL" ? undefined : f.country })}`),
  forecast: (f: Filters) =>
    get(`/api/forecast?${qs({ reporting: f.reporting, scenario: f.scenario, country: f.country === "ALL" ? undefined : f.country })}`),
  wc: (f: Filters, dso?: number, dpo?: number, inv?: number) =>
    get(`/api/working-capital?${qs({ reporting: f.reporting, country: f.country === "ALL" ? undefined : f.country, dso, dpo, inventory_days: inv })}`),
  receivables: (f: Filters) =>
    get(`/api/receivables?${qs({ reporting: f.reporting, country: f.country === "ALL" ? undefined : f.country })}`),
  payables: (f: Filters, timing = "terms") =>
    get(`/api/payables?${qs({ reporting: f.reporting, country: f.country === "ALL" ? undefined : f.country, timing })}`),
  pooling: (f: Filters, extra: Record<string, string | number | undefined> = {}) =>
    get(`/api/pooling?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy, ...extra })}`),
  investments: (f: Filters, extra: Record<string, string | number | undefined> = {}) =>
    get(`/api/investments?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy, ...extra })}`),
  borrowing: (f: Filters, extra: Record<string, string | number | undefined> = {}) =>
    get(`/api/borrowing?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy, ...extra })}`),
  fx: (f: Filters, extra: Record<string, string | number | undefined> = {}) =>
    get(`/api/fx?${qs({ reporting: f.reporting, scenario: f.scenario, ...extra })}`),
  strategy: (f: Filters) => get(`/api/strategy-comparison?${qs({ reporting: f.reporting, scenario: f.scenario })}`),
  optimize: (body: unknown) => post(`/api/optimize`, body),
  scenario: (body: unknown) => post(`/api/scenario`, body),
  research: (body: unknown) => post(`/api/research`, body),
  methodology: () => get(`/api/methodology`),
  matrix: (f: Filters) =>
    get(`/api/matrix?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy })}`),
  concentration: (f: Filters) => get(`/api/concentration?${qs({ reporting: f.reporting })}`),
  country: (code: string, f: Filters) =>
    get(`/api/country/${code}?${qs({ reporting: f.reporting, scenario: f.scenario, strategy: f.strategy })}`),
  sankey: (f: Filters) => get(`/api/sankey?${qs({ reporting: f.reporting, strategy: f.strategy })}`),
  events: (month?: string) => get(`/api/events?${qs({ month })}`),
  countries: () => get(`/api/countries`),
  game: (body: unknown) => post(`/api/game`, body),
};
