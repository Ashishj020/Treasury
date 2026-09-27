import { useState } from "react";
import { api } from "../lib/api";
import { formatPct, money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { Bars, Lines } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Segment, Skeleton, SliderRow, Stat } from "../components/ui/primitives";

export function FX() {
  const t = useTreasury();
  const [usd, setUsd] = useState(83);
  const [style, setStyle] = useState("partial");
  const [ratio, setRatio] = useState(50);
  const { data, error, loading } = useApi(
    () =>
      api.fx(
        { reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country },
        { usd_inr: usd, hedge_style: style, hedge_ratio: ratio / 100 }
      ),
    [t.reporting, t.scenario, usd, style, ratio]
  );
  if (loading) return <Skeleton className="h-[60vh]" />;
  if (error || !data) return <ErrorState message={error || ""} />;
  const d = data as any;
  return (
    <div className="space-y-6">
      <Eyebrow>08 · FX exposure</Eyebrow>
      <h1 className="font-display text-3xl">Try a 10% INR shock. Watch group liquidity.</h1>
      <p className="text-sm text-mute">{d.disclaimer}</p>
      <div className="grid gap-3 md:grid-cols-3">
        <Panel>
          <Stat label="Transaction" value={money(d.transaction, d.meta.symbol, d.meta.unit)} hint={d.definitions.transaction} />
        </Panel>
        <Panel>
          <Stat label="Translation" value={money(d.translation, d.meta.symbol, d.meta.unit)} hint={d.definitions.translation} />
        </Panel>
        <Panel>
          <Stat label="Economic" value={money(d.economic, d.meta.symbol, d.meta.unit)} hint={d.definitions.economic} />
        </Panel>
      </div>
      <Panel>
        <h2 className="font-display text-xl">USD/INR slider</h2>
        <SliderRow label="USD/INR" min={75} max={95} step={0.5} value={usd} onChange={setUsd} />
        <Bars
          data={d.slider}
          x="usd_inr"
          series={[
            { key: "cash", color: "#22D3EE", name: "Group cash" },
            { key: "delta", color: "#F472B6", name: "Δ vs spot path" },
          ]}
        />
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-display text-xl">Natural hedge</h2>
          <p className="text-sm text-mute">{d.natural_hedge.explain}</p>
          <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
            <div>USD in {money(d.natural_hedge.usd_inflows, d.meta.symbol, d.meta.unit)}</div>
            <div>USD out {money(d.natural_hedge.usd_outflows, d.meta.symbol, d.meta.unit)}</div>
            <div>Net {money(d.natural_hedge.net, d.meta.symbol, d.meta.unit)}</div>
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-xl">Hedge sleeve</h2>
          <Segment
            value={style}
            onChange={setStyle}
            options={[
              { id: "unhedged", label: "Unhedged" },
              { id: "natural", label: "Natural" },
              { id: "forward", label: "Forward" },
              { id: "partial", label: "Partial" },
            ]}
          />
          <div className="mt-4">
            <SliderRow label="Hedge ratio" min={0} max={100} step={25} value={ratio} onChange={setRatio} suffix="%" />
          </div>
          <p className="mt-3 text-[12px] text-mute">{d.hedge.explain[style]} Residual {money(d.hedge.residual, d.meta.symbol, d.meta.unit)} · cost {money(d.hedge.cost, d.meta.symbol, d.meta.unit)}.</p>
        </Panel>
      </div>
      <Panel>
        <h2 className="font-display text-xl">Stress tests</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead className="text-[10px] uppercase tracking-wider text-faint">
              <tr>
                <th className="py-2 text-left">Shock</th>
                <th className="text-right">Before</th>
                <th className="text-right">After</th>
                <th className="text-right">Δ</th>
                <th className="text-right">%</th>
              </tr>
            </thead>
            <tbody>
              {d.stress.map((s: any, i: number) => (
                <tr key={i} className="border-t border-white/5">
                  <td className="py-2">{s.label}</td>
                  <td className="num text-right">{s.before.toFixed(1)}</td>
                  <td className="num text-right">{s.after.toFixed(1)}</td>
                  <td className="num text-right">{s.change.toFixed(1)}</td>
                  <td className="num text-right">{formatPct(s.change_pct)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <Panel>
        <h2 className="font-display text-xl">Rate history</h2>
        <Lines
          data={d.history}
          x="period"
          series={[
            { key: "USDINR", color: "#22D3EE", name: "USD/INR" },
            { key: "GBPINR", color: "#8B5CF6", name: "GBP/INR" },
            { key: "SGDINR", color: "#34D399", name: "SGD/INR" },
          ]}
        />
        <Learn on={t.learning}>INR value = foreign amount × FX rate. Crosses are derived. No forward curve in this project model.</Learn>
      </Panel>
    </div>
  );
}
