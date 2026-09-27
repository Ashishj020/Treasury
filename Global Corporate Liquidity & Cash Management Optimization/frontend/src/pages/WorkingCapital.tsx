import { useState } from "react";
import { api } from "../lib/api";
import { formatNum, money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { Bars, Donut, Lines, WaterfallChart } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Segment, Skeleton, SliderRow, Stat } from "../components/ui/primitives";

export function WorkingCapital() {
  const t = useTreasury();
  const [dso, setDso] = useState<number | undefined>();
  const [dpo, setDpo] = useState<number | undefined>();
  const [inv, setInv] = useState<number | undefined>();
  const [timing, setTiming] = useState("terms");
  const wc = useApi(
    () => api.wc({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }, dso, dpo, inv),
    [t.reporting, t.country, dso, dpo, inv]
  );
  const ar = useApi(
    () => api.receivables({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.country]
  );
  const ap = useApi(
    () => api.payables({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }, timing),
    [t.reporting, t.country, timing]
  );
  if (wc.loading || !wc.data) return wc.error ? <ErrorState message={wc.error} /> : <Skeleton className="h-[60vh]" />;
  const d = wc.data as any;
  const meta = d.meta;
  const base = d.base;
  return (
    <div className="space-y-6">
      <Eyebrow>04 · Working capital</Eyebrow>
      <h1 className="font-display text-3xl">Pull cash out of the cycle — without new capital</h1>
      <div className="grid gap-3 md:grid-cols-4">
        <Panel>
          <Stat label="DSO" value={`${formatNum(d.adjusted.dso, 1)}d`} hint={d.explain.dso} />
        </Panel>
        <Panel>
          <Stat label="DPO" value={`${formatNum(d.adjusted.dpo, 1)}d`} hint={d.explain.dpo} />
        </Panel>
        <Panel>
          <Stat label="CCC" value={`${formatNum(d.adjusted.ccc, 1)}d`} hint={d.explain.ccc} />
        </Panel>
        <Panel>
          <Stat
            label="Cash potentially released"
            value={money(d.released.total, meta.symbol, meta.unit)}
            tone={d.released.total >= 0 ? "pos" : "neg"}
          />
        </Panel>
      </div>

      <Panel>
        <h2 className="font-display text-xl">Move the days</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <SliderRow label="DSO" min={20} max={80} step={1} value={dso ?? Math.round(base.dso)} onChange={setDso} suffix="d" />
          <SliderRow label="DPO" min={15} max={75} step={1} value={dpo ?? Math.round(base.dpo)} onChange={setDpo} suffix="d" />
          <SliderRow label="Inventory days" min={10} max={80} step={1} value={inv ?? Math.round(base.inventory_days)} onChange={setInv} suffix="d" />
        </div>
        <Learn on={t.learning}>
          DSO = Average AR / Revenue × 365. Cutting DSO by 5 days releases ≈ Revenue × 5 / 365. Paying later than contract is not a strategy in this lab.
        </Learn>
      </Panel>

      <Panel>
        <h2 className="font-display text-xl">Working-capital bridge</h2>
        <WaterfallChart data={(d.bridge || []).map((b: any) => ({ label: b.label, value: b.value, type: b.label.includes("Starting") || b.label.includes("Ending") ? "total" : "flow" }))} />
      </Panel>

      <Panel>
        <h2 className="font-display text-xl">CCC trend</h2>
        <Lines
          data={d.trend || []}
          x="period"
          series={[
            { key: "dso", color: "#22D3EE", name: "DSO" },
            { key: "dpo", color: "#34D399", name: "DPO" },
            { key: "ccc", color: "#C084FC", name: "CCC" },
          ]}
        />
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-display text-xl">Receivables aging</h2>
          {ar.data && (
            <>
              <Donut
                data={(ar.data as any).buckets.map((b: any, i: number) => ({
                  name: b.bucket,
                  value: b.amount,
                  color: ["#22D3EE", "#34D399", "#F472B6", "#8B5CF6"][i % 4],
                }))}
              />
              <p className="text-[12px] text-mute">{(ar.data as any).why} Overdue {money((ar.data as any).overdue, meta.symbol, meta.unit)}.</p>
            </>
          )}
        </Panel>
        <Panel>
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl">Payables timing</h2>
            <Segment
              value={timing}
              onChange={setTiming}
              options={[
                { id: "immediate", label: "Immediate" },
                { id: "terms", label: "On terms" },
                { id: "optimize", label: "Optimize" },
              ]}
            />
          </div>
          {ap.data && (
            <>
              <Bars
                data={(ap.data as any).status}
                x="status"
                series={[{ key: "amount", color: "#6366F1", name: "AP" }]}
                height={180}
              />
              <p className="mt-2 text-[12px] text-mute">
                Liquidity impact {money((ap.data as any).liquidity_impact, meta.symbol, meta.unit)}. {(ap.data as any).note}
              </p>
            </>
          )}
        </Panel>
      </div>
    </div>
  );
}
