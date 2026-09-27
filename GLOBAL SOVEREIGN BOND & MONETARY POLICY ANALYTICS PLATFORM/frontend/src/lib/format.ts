export const MARKETS = ["US", "IN", "UK", "EZ"] as const;
export type Mkt = (typeof MARKETS)[number];

export const MARKET_META: Record<Mkt, { name: string; short: string; color: string; cb: string }> = {
  US: { name: "United States", short: "US", color: "#22D3EE", cb: "FED" },
  IN: { name: "India", short: "INDIA", color: "#F472B6", cb: "RBI" },
  UK: { name: "United Kingdom", short: "UK", color: "#34D399", cb: "BOE" },
  EZ: { name: "Eurozone", short: "EUROZONE", color: "#A78BFA", cb: "ECB" },
};

export function fmtPct(n: number | null | undefined, d = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${n.toFixed(d)}%`;
}

export function fmtBp(n: number | null | undefined, d = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(d)} bp`;
}

export function fmtNum(n: number | null | undefined, d = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(d);
}

export function tone(n: number | null | undefined) {
  if (n === null || n === undefined) return "text-mist-400";
  if (n > 0) return "text-negative";
  if (n < 0) return "text-positive";
  return "text-mist-400";
}

/** Yield UP is usually bad for long bonds — we colour yield increases as rose. */
export const negative = "text-[#FB7185]";
export const positive = "text-emerald";
