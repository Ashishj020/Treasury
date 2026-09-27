import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { formatNum, formatPct, money, statusColor } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { Bars, Spark } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Skeleton, Stat, Tip } from "../components/ui/primitives";

const KPI_META: Record<string, { title: string; tip: string }> = {
  cash: { title: "Total cash", tip: "Group closing cash in the selected reporting currency." },
  inflows: { title: "Total inflows", tip: "Monthly receipts — customers, collections, interest, other." },
  outflows: { title: "Total outflows", tip: "Suppliers, payroll, tax, capex, debt service, opex." },
  idle: { title: "Idle cash", tip: "Closing − required operating cash − invested. Cash sitting unused." },
  funding: { title: "Funding gap", tip: "Where closing cash is below the minimum buffer." },
  fx: { title: "FX exposure", tip: "Unhedged transactional exposure, converted." },
  invested: { title: "Short-term investments", tip: "Illustrative treasury allocation — not a recommendation." },
  financing: { title: "Financing cost", tip: "Interest Expense = Borrowing × Rate × Time." },
};

export function Overview() {
  const t = useTreasury();
  const nav = useNavigate();
  const { data, error, loading } = useApi(
    () => api.overview({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.scenario, t.strategy, t.country]
  );

  if (loading) return <Skeleton className="h-[70vh]" />;
  if (error || !data) return <ErrorState message={error || "empty"} />;

  const d = data as any;
  const meta = d.meta;
  const map = d.map as any[];
  const kpis = d.kpis as any[];
  const status = d.status;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Eyebrow>01 · Command center</Eyebrow>
          <h1 className="font-display text-3xl md:text-4xl">Where cash sits. Where cash moves. Where cash gets stuck.</h1>
          <p className="mt-2 max-w-2xl text-sm text-mute">
            Orion Global · as-of {d.as_of} · {meta.disclaimer}. Annual simulated 2025 inflows {money(d.annual_flow_inr.inflows, "₹", "Cr")}.
          </p>
        </div>
        <div className="min-w-[180px] text-left lg:text-right">
          <div className="text-[10px] uppercase tracking-[0.2em] text-faint">Liquidity status</div>
          <div className="mt-1 font-display text-xl" style={{ color: statusColor(status.code) }}>
            {status.code === "SAFE" ? "SAFE" : status.code === "WATCH" ? "WATCH" : status.code === "TIGHT" ? "TIGHT" : "FUNDING REQUIRED"}
          </div>
          <p className="max-w-xs text-[11px] text-mute">{status.why}</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map((k) => {
          const m = KPI_META[k.key];
          return (
            <Panel key={k.key}>
              <div className="flex items-start justify-between">
                <div className="text-[10px] uppercase tracking-[0.18em] text-faint">
                  {m?.title || k.key}
                  <Tip title={m?.title || k.key}>{k.definition}</Tip>
                </div>
                <span className={`text-[11px] ${k.change >= 0 ? "text-emerald" : "text-danger"}`}>{formatPct(k.change)}</span>
              </div>
              <div className="num mt-2 text-[28px] leading-none">
                {money(k.value, meta.symbol, meta.unit)}
              </div>
              <div className="mt-2">
                <Spark data={k.spark || []} color={k.key === "idle" ? "#A7F3D0" : k.key === "funding" ? "#F472B6" : "#22D3EE"} />
              </div>
            </Panel>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
        <Panel>
          <Eyebrow>Cash map</Eyebrow>
          <h2 className="font-display text-xl">Click a jurisdiction</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {map.map((c) => (
              <button
                key={c.country}
                type="button"
                onClick={() => {
                  t.setCountry(c.country);
                  nav("/liquidity");
                }}
                className="border border-white/10 p-4 text-left transition hover:border-cyan/40"
              >
                <div className="flex items-center justify-between">
                  <div className="font-display text-lg">{c.country}</div>
                  <span className="text-[11px] text-mute">{c.personality}</span>
                </div>
                <div className="num mt-2 text-2xl">{money(c.closing, meta.symbol, meta.unit)}</div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-[11px] text-mute">
                  <div>Min {formatNum(c.min_cash)}</div>
                  <div>Surplus {formatNum(c.surplus)}</div>
                  <div>Idle {formatNum(c.idle)}</div>
                  <div>Funding {formatNum(c.funding)}</div>
                </div>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full"
                    style={{
                      width: `${Math.min(100, (c.closing / (c.min_cash || 1)) * 40)}%`,
                      background: statusColor(c.status),
                    }}
                  />
                </div>
              </button>
            ))}
          </div>
          <Learn on={t.learning}>
            Node colour follows the traffic-light rule: surplus ≥ 15% of min cash is SAFE. A funding gap versus the buffer turns TIGHT or FUNDING REQUIRED.
          </Learn>
        </Panel>

        <div className="space-y-4">
          <Panel>
            <Eyebrow>Cash runway</Eyebrow>
            <Stat label="Days of operating outflow" value={`${formatNum(d.runway_days, 0)}d`} hint="Available cash / average daily outflow" />
            <p className="mt-3 text-[11px] text-mute">
              Ignores restricted cash, undrawn revolvers, and intra-month timing. A desk metric, not a covenant test.
            </p>
          </Panel>
          <Panel>
            <Eyebrow>Alerts</Eyebrow>
            <ul className="space-y-2 text-[13px] text-mute">
              {(d.notes || []).slice(0, 4).map((n: string, i: number) => (
                <li key={i} className="border-l border-white/10 pl-3">
                  {n}
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      <Panel>
        <Eyebrow>Twelve-month path</Eyebrow>
        <h2 className="font-display text-xl">Group cash, idle cash, funding</h2>
        <Bars
          data={(d.spark || []).map((s: any) => ({ ...s, period: s.period.slice(0, 7) }))}
          x="period"
          series={[
            { key: "cash", color: "#22D3EE", name: "Cash" },
            { key: "idle", color: "#A7F3D0", name: "Idle" },
            { key: "funding", color: "#F472B6", name: "Funding" },
          ]}
          height={260}
        />
      </Panel>
    </div>
  );
}
