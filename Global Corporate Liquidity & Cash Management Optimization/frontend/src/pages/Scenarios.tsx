import { useState } from "react";
import { api } from "../lib/api";
import { money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { ErrorState, Eyebrow, Panel, Skeleton, SliderRow, Stat } from "../components/ui/primitives";

export function Scenarios() {
  const t = useTreasury();
  const [coll, setColl] = useState(1);
  const [out, setOut] = useState(1);
  const [bp, setBp] = useState(0);
  const [fx, setFx] = useState(0);
  const [delay, setDelay] = useState(0);
  const { data, error, loading } = useApi(
    () =>
      api.scenario({
        scenario: t.scenario,
        reporting: t.reporting,
        strategy: t.strategy,
        collection_factor: coll,
        outflow_factor: out,
        rate_shift_bp: bp,
        fx_inr_shock: fx,
        receivable_delay_days: delay,
      }),
    [t.reporting, t.scenario, t.strategy, coll, out, bp, fx, delay]
  );
  if (loading) return <Skeleton className="h-[50vh]" />;
  if (error || !data) return <ErrorState message={error || ""} />;
  const d = data as any;
  const s = d.survival;
  return (
    <div className="space-y-6">
      <Eyebrow>09 · Scenario lab</Eyebrow>
      <h1 className="font-display text-3xl">What happens under a recession path?</h1>
      <div className="flex gap-2">
        {(["base", "optimistic", "stressed"] as const).map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              t.setScenario(id);
              if (id === "base") {
                setColl(1); setOut(1); setBp(0); setFx(0); setDelay(0);
              }
              if (id === "optimistic") {
                setColl(1.06); setOut(0.96); setBp(-25); setFx(-0.02); setDelay(-4);
              }
              if (id === "stressed") {
                setColl(0.88); setOut(1.1); setBp(150); setFx(0.08); setDelay(15);
              }
            }}
            className={`rounded-full border px-3 py-1 text-[12px] uppercase ${t.scenario === id ? "border-cyan text-cyan" : "border-white/10 text-mute"}`}
          >
            {id}
          </button>
        ))}
      </div>
      <Panel className="grid gap-3 md:grid-cols-2">
        <SliderRow label="Collections ×" min={0.7} max={1.2} step={0.01} value={coll} onChange={setColl} />
        <SliderRow label="Outflows ×" min={0.8} max={1.3} step={0.01} value={out} onChange={setOut} />
        <SliderRow label="Rates shift (bp)" min={-50} max={250} step={5} value={bp} onChange={setBp} />
        <SliderRow label="INR FX shock" min={-0.12} max={0.12} step={0.01} value={fx} onChange={setFx} />
        <SliderRow label="Receivable delay (days)" min={-10} max={25} step={1} value={delay} onChange={setDelay} />
      </Panel>
      <div className="grid gap-3 md:grid-cols-2">
        <Panel>
          <h2 className="font-display text-lg">Before</h2>
          <div className="mt-2 space-y-1 text-sm text-mute">
            <div>Cash {money(d.before.cash, d.meta.symbol, d.meta.unit)}</div>
            <div>Idle {money(d.before.idle, d.meta.symbol, d.meta.unit)}</div>
            <div>Funding {money(d.before.funding, d.meta.symbol, d.meta.unit)}</div>
            <div>FX {money(d.before.fx, d.meta.symbol, d.meta.unit)}</div>
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-lg">After shock</h2>
          <div className="mt-2 space-y-1 text-sm text-mute">
            <div>Cash {money(d.after.cash, d.meta.symbol, d.meta.unit)}</div>
            <div>Idle {money(d.after.idle, d.meta.symbol, d.meta.unit)}</div>
            <div>Funding {money(d.after.funding, d.meta.symbol, d.meta.unit)}</div>
            <div>FX {money(d.after.fx, d.meta.symbol, d.meta.unit)}</div>
          </div>
        </Panel>
      </div>
      <Panel>
        <Eyebrow>Survival check</Eyebrow>
        <div className={`font-display text-2xl ${s.breach ? "text-danger" : "text-emerald"}`}>
          {s.breach ? "⚠ BUFFER BREACH" : "BUFFER HOLDS"}
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <Stat label="Minimum liquidity buffer" value={money(s.min_buffer, d.meta.symbol, d.meta.unit)} />
          <Stat label="Projected lowest cash" value={money(s.projected_low, d.meta.symbol, d.meta.unit)} />
          <Stat label="Runway" value={`${s.runway_days.toFixed(0)}d`} />
        </div>
        <ul className="mt-4 space-y-1 text-sm text-mute">
          {d.suggestions.map((x: string) => (
            <li key={x}>→ {x}</li>
          ))}
        </ul>
        <p className="mt-3 text-[11px] text-faint">{d.disclaimer}</p>
      </Panel>
    </div>
  );
}
