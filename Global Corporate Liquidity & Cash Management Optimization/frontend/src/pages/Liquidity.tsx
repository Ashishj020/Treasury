import { api } from "../lib/api";
import { formatNum, money, statusColor } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { LineArea } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Skeleton, Stat } from "../components/ui/primitives";

export function Liquidity() {
  const t = useTreasury();
  const liq = useApi(
    () => api.liquidity({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.scenario, t.strategy, t.country]
  );
  const fc = useApi(
    () => api.forecast({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.scenario, t.country]
  );
  if (liq.loading || fc.loading) return <Skeleton className="h-[60vh]" />;
  if (liq.error || !liq.data) return <ErrorState message={liq.error || ""} />;
  const d = liq.data as any;
  const f = (fc.data as any) || { horizon: [] };
  const heat = d.heatmap as any[];
  const months = Array.from(new Set(heat.map((h) => h.period)));
  const countries = Array.from(new Set(heat.map((h) => h.country)));
  const rank = d.idle_ranking as any[];
  const meta = d.meta;

  return (
    <div className="space-y-6">
      <Eyebrow>03 · Liquidity</Eyebrow>
      <h1 className="font-display text-3xl">How much cash is actually idle?</h1>
      <div className="grid gap-3 md:grid-cols-3">
        <Panel>
          <Stat label="Liquidity gap" value={money(d.gap, meta.symbol, meta.unit)} hint="Available + inflows − outflows − min cash" />
        </Panel>
        <Panel>
          <Stat label="Cash runway" value={`${formatNum(d.runway_days, 0)} days`} hint={d.runway_note} />
        </Panel>
        <Panel>
          <Stat label="Idle cash" value={money(d.totals.idle, meta.symbol, meta.unit)} tone="idle" />
        </Panel>
      </div>

      <Panel>
        <h2 className="font-display text-xl">Where is cash getting stuck?</h2>
        <ol className="mt-4 space-y-2">
          {rank.map((r, i) => (
            <li key={r.country} className="flex items-center justify-between border-b border-white/5 py-2">
              <span className="text-mute">
                {i + 1}. {r.country} · {r.personality}
              </span>
              <span className="num">{money(r.idle, meta.symbol, meta.unit)}</span>
            </li>
          ))}
        </ol>
        <Learn on={t.learning}>
          Idle cash = closing − operating requirement − invested. India usually ranks first because surplus sits above a 60 Cr buffer.
        </Learn>
      </Panel>

      <Panel>
        <h2 className="font-display text-xl">Country × month heatmap</h2>
        <p className="mb-3 text-[12px] text-mute">Colour is surplus (mint) versus deficit (pink). This is where and when cash pressure shows up.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-[10px]">
            <thead>
              <tr>
                <th className="p-1 text-left text-faint"> </th>
                {months.map((m) => (
                  <th key={m} className="p-1 font-normal text-faint">
                    {String(m).slice(2)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {countries.map((c) => (
                <tr key={c}>
                  <td className="pr-2 text-mute">{c}</td>
                  {months.map((m) => {
                    const cell = heat.find((h) => h.country === c && h.period === m);
                    const net = cell?.net || 0;
                    const bg = net >= 0 ? `rgba(52,211,153,${Math.min(0.55, 0.08 + net / 80)})` : `rgba(244,114,182,${Math.min(0.55, 0.08 + Math.abs(net) / 80)})`;
                    return (
                      <td key={m} title={`${c} ${m}: ${formatNum(net)}`} className="h-6 w-6" style={{ background: bg }} />
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel>
        <h2 className="font-display text-xl">12-month liquidity forecast</h2>
        <LineArea
          data={f.horizon || []}
          x="period"
          series={[
            { key: "closing", color: "#22D3EE", name: "Base" },
            { key: "optimistic", color: "#34D399", name: "Optimistic" },
            { key: "stressed", color: "#F472B6", name: "Stressed" },
            { key: "min_cash", color: "#8B5CF6", name: "Min cash" },
          ]}
          height={280}
        />
      </Panel>

      <div className="grid gap-3 md:grid-cols-2">
        {(d.positions || []).map((p: any) => (
          <Panel key={p.country}>
            <div className="flex justify-between">
              <h3 className="font-display text-lg">{p.country} treasury</h3>
              <span style={{ color: statusColor(p.status) }}>{p.status}</span>
            </div>
            <p className="text-[11px] text-mute">{p.personality}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-[12px]">
              <div>Cash {money(p.closing, meta.symbol, meta.unit)}</div>
              <div>Min {formatNum(p.min_cash)}</div>
              <div>Idle {formatNum(p.idle)}</div>
              <div>Funding {formatNum(p.funding)}</div>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
