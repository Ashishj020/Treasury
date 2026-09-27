export type Reporting = "INR" | "USD" | "GBP" | "SGD";
export type Scenario = "base" | "optimistic" | "stressed";
export type Strategy = "none" | "physical" | "notional" | "hybrid";
export type CountryCode = "IN" | "US" | "UK" | "SG" | "ALL";

export const COUNTRIES: { code: CountryCode; name: string; tag: string }[] = [
  { code: "ALL", name: "Group", tag: "GLOBAL" },
  { code: "IN", name: "India", tag: "INR · Cash Rich" },
  { code: "US", name: "United States", tag: "USD · Always Moving" },
  { code: "UK", name: "United Kingdom", tag: "GBP · Buffer Builder" },
  { code: "SG", name: "Singapore", tag: "SGD · Efficient but Tight" },
];

export const NAV = [
  { id: "01", to: "/overview", label: "Overview" },
  { id: "02", to: "/cash-flows", label: "Cash Flows" },
  { id: "03", to: "/liquidity", label: "Liquidity" },
  { id: "04", to: "/working-capital", label: "Working Capital" },
  { id: "05", to: "/pooling", label: "Cash Pooling" },
  { id: "06", to: "/investments", label: "Investments" },
  { id: "07", to: "/borrowing", label: "Borrowing" },
  { id: "08", to: "/fx", label: "FX Exposure" },
  { id: "09", to: "/scenarios", label: "Scenarios" },
  { id: "10", to: "/strategy", label: "Strategy Lab" },
  { id: "11", to: "/research", label: "Research" },
  { id: "12", to: "/methodology", label: "Methodology" },
];

export function formatNum(n: number | undefined | null, digits = 1): string {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  const sign = n < 0 ? "−" : "";
  if (abs >= 1000) return sign + abs.toFixed(0);
  if (abs >= 100) return sign + abs.toFixed(Math.min(digits, 1));
  return sign + abs.toFixed(digits);
}

export function formatPct(n: number | undefined | null, digits = 1): string {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  const v = Math.abs(n) <= 2 ? n * 100 : n;
  const sign = v > 0 ? "+" : v < 0 ? "−" : "";
  return `${sign}${Math.abs(v).toFixed(digits)}%`;
}

export function money(n: number, symbol: string, unit: string, digits = 1): string {
  return `${symbol}${formatNum(n, digits)} ${unit}`;
}

export function statusColor(code: string): string {
  if (code === "SAFE") return "#34D399";
  if (code === "WATCH") return "#F472B6";
  if (code === "TIGHT") return "#FB923C";
  return "#C084FC";
}

export const qs = (p: Record<string, string | number | undefined | null>) => {
  const u = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") u.set(k, String(v));
  });
  return u.toString();
};
