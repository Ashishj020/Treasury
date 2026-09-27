import { useState } from "react";
import { api } from "../lib/api";
import { formatNum, money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { Bars } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Skeleton, SliderRow, Stat, Table } from "../components/ui/primitives";

export function Investments() {
  const t = useTreasury();
  const [instrument, setInstrument] = useState("mmf");
  const [horizon, setHorizon] = useState(90);
  const { data, error, loading } = useApi(
    () =>
      api.investments(
        { reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country },
        { instrument, horizon_days: horizon }
      ),
    [t.reporting, t.scenario, t.strategy, instrument, horizon]
  );
  if (loading) return <Skeleton className="h-[50vh]" />;
  if (error || !data) return <ErrorState message={error || ""} />;
  const d = data as any;
  return (
    <div className="space-y-6">
      <Eyebrow>06 · Short-term investment lab</Eyebrow>
      <h1 className="font-display text-3xl">Where can excess cash be invested?</h1>
      <p className="text-sm text-pink">{d.label} {d.disclaimer}</p>
      <div className="grid gap-3 md:grid-cols-3">
        <Panel>
          <Stat label="Available surplus" value={money(d.available_surplus, d.meta.symbol, d.meta.unit)} />
        </Panel>
        <Panel>
          <Stat label="Expected interest income" value={money(d.expected_income, d.meta.symbol, d.meta.unit)} tone="pos" />
        </Panel>
        <Panel>
          <Stat label="Opportunity cost vs 5.6%" value={money(d.opportunity_cost, d.meta.symbol, d.meta.unit)} />
        </Panel>
      </div>
      <Panel>
        <SliderRow label="Horizon" min={1} max={180} step={1} value={horizon} onChange={setHorizon} suffix="d" />
        <div className="mt-4 flex flex-wrap gap-2">
          {d.options.map((o: any) => (
            <button
              key={o.id}
              type="button"
              onClick={() => setInstrument(o.id)}
              className={`rounded-full border px-3 py-1 text-[12px] ${instrument === o.id ? "border-cyan text-cyan" : "border-white/10 text-mute"}`}
            >
              {o.name}
            </button>
          ))}
        </div>
        <Bars data={d.options} x="name" series={[{ key: "income", color: "#34D399", name: "Income" }]} height={220} />
        <Table
          columns={[
            { key: "name", label: "Instrument" },
            { key: "horizon_days", label: "Days", align: "right" },
            { key: "yield_pct", label: "Yield", align: "right" },
            { key: "income", label: "Income", align: "right" },
            { key: "note", label: "Note" },
          ]}
          rows={d.options.map((o: any) => ({
            name: o.name,
            horizon_days: o.horizon_days,
            yield_pct: `${(o.yield_pct * 100).toFixed(1)}%`,
            income: formatNum(o.income),
            note: o.note,
          }))}
        />
        <Learn on={t.learning}>{d.liquidity_impact} Interest Income = Invested × Yield × Time.</Learn>
      </Panel>
    </div>
  );
}

export function Borrowing() {
  const t = useTreasury();
  const [tenor, setTenor] = useState(90);
  const [facility, setFacility] = useState("rcf_in");
  const { data, error, loading } = useApi(
    () =>
      api.borrowing(
        { reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country },
        { tenor_days: tenor, facility }
      ),
    [t.reporting, t.scenario, t.strategy, tenor, facility]
  );
  if (loading) return <Skeleton className="h-[50vh]" />;
  if (error || !data) return <ErrorState message={error || ""} />;
  const d = data as any;
  return (
    <div className="space-y-6">
      <Eyebrow>07 · Borrowing optimizer</Eyebrow>
      <h1 className="font-display text-3xl">Borrow locally, pool it, or fund intercompany?</h1>
      <div className="grid gap-3 md:grid-cols-3">
        <Panel>
          <Stat label="Funding need" value={money(d.funding_need, d.meta.symbol, d.meta.unit)} tone="warn" />
        </Panel>
        <Panel>
          <Stat label="Avoided by pooling" value={money(d.avoided_by_pooling, d.meta.symbol, d.meta.unit)} tone="pos" />
        </Panel>
        <Panel>
          <Stat label="Interest cost" value={money(d.interest_cost, d.meta.symbol, d.meta.unit)} hint={d.formula} />
        </Panel>
      </div>
      <Panel>
        <SliderRow label="Tenor" min={30} max={365} step={5} value={tenor} onChange={setTenor} suffix="d" />
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {d.compare.map((c: any) => (
            <div key={c.path} className="border border-white/10 p-4">
              <div className="text-[11px] uppercase tracking-wider text-faint">{c.path}</div>
              <div className="num mt-2 text-xl">{money(c.cost, d.meta.symbol, d.meta.unit)}</div>
              <p className="mt-2 text-[12px] text-mute">{c.note}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {d.facilities.map((f: any) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFacility(f.id)}
              className={`rounded-full border px-3 py-1 text-[12px] ${facility === f.id ? "border-cyan text-cyan" : "border-white/10 text-mute"}`}
            >
              {f.name}
            </button>
          ))}
        </div>
      </Panel>
    </div>
  );
}
