import { useState } from "react";
import { api } from "../lib/api";
import { money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { Bars, LineArea, WaterfallChart } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Segment, Skeleton } from "../components/ui/primitives";

export function CashFlows() {
  const t = useTreasury();
  const [gran, setGran] = useState<"month" | "day">("month");
  const { data, error, loading } = useApi(
    () =>
      api.cashFlows(
        { reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country },
        { granularity: gran }
      ),
    [t.reporting, t.scenario, t.country, gran]
  );
  if (loading) return <Skeleton className="h-[60vh]" />;
  if (error || !data) return <ErrorState message={error || ""} />;
  const d = data as any;
  const monthly = (d.series || []).filter((s: any) => gran === "day" || true);
  const byPeriod: Record<string, any> = {};
  for (const s of monthly) {
    const k = s.period.slice(0, gran === "day" ? 10 : 7);
    byPeriod[k] ??= { period: k, inflows: 0, outflows: 0, closing: 0 };
    byPeriod[k].inflows += s.inflows;
    byPeriod[k].outflows += s.outflows;
    byPeriod[k].closing = s.closing;
  }
  const series = Object.values(byPeriod);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Eyebrow>02 · Cash flows</Eyebrow>
          <h1 className="font-display text-3xl">Opening + inflows − outflows = closing</h1>
        </div>
        <Segment
          value={gran}
          onChange={setGran}
          options={[
            { id: "month", label: "Monthly" },
            { id: "day", label: "Daily (Sep 26)" },
          ]}
        />
      </div>
      <Panel>
        <h2 className="font-display text-xl">Inflows vs outflows</h2>
        <Bars
          data={series}
          x="period"
          series={[
            { key: "inflows", color: "#34D399", name: "Inflows" },
            { key: "outflows", color: "#FB7185", name: "Outflows" },
          ]}
          height={280}
        />
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-display text-xl">Waterfall · last period</h2>
          <WaterfallChart data={d.waterfall || []} />
          <Learn on={t.learning}>
            Hover each bar. Inflows add; payroll, tax, capex and debt service subtract. Closing is a total, not a stack.
          </Learn>
        </Panel>
        <Panel>
          <h2 className="font-display text-xl">Closing cash</h2>
          <LineArea data={series} x="period" series={[{ key: "closing", color: "#22D3EE", name: "Closing" }]} />
          <p className="mt-3 text-[12px] text-mute">
            Totals this view: inflows {money(d.totals?.inflows || 0, d.meta.symbol, d.meta.unit)} · outflows{" "}
            {money(d.totals?.outflows || 0, d.meta.symbol, d.meta.unit)}
          </p>
        </Panel>
      </div>
    </div>
  );
}
