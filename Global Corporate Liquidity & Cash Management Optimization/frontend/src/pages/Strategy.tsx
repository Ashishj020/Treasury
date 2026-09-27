import { useState } from "react";
import { api } from "../lib/api";
import { formatNum, formatPct, money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { Bars, WaterfallChart } from "../components/charts/Charts";
import { ErrorState, Eyebrow, Learn, Panel, Skeleton, SliderRow, Stat, Table } from "../components/ui/primitives";

export function Strategy() {
  const t = useTreasury();
  const [wL, setWL] = useState(40);
  const [wC, setWC] = useState(30);
  const [wF, setWF] = useState(20);
  const [wR, setWR] = useState(10);
  const pack = useApi(
    () => api.strategy({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.scenario]
  );
  const opt = useApi(
    () =>
      api.optimize({
        reporting: t.reporting,
        scenario: t.scenario,
        liquidity: wL / 100,
        cost: wC / 100,
        fx: wF / 100,
        return: wR / 100,
      }),
    [t.reporting, t.scenario, wL, wC, wF, wR]
  );
  const matrix = useApi(
    () => api.matrix({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.scenario, t.strategy]
  );
  const conc = useApi(() => api.concentration({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }), [
    t.reporting,
  ]);
  const sankey = useApi(
    () => api.sankey({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }),
    [t.reporting, t.strategy]
  );
  const events = useApi(() => api.events("2026-09"), []);
  const [choice, setChoice] = useState<string | null>(null);
  const [game, setGame] = useState<any>(null);

  if (pack.loading || opt.loading) return <Skeleton className="h-[60vh]" />;
  if (pack.error || !pack.data) return <ErrorState message={pack.error || ""} />;
  const d = pack.data as any;
  const o = (opt.data as any) || {};
  const rec = d.recommended;
  const ba = o.before_after || { before: {}, after: {} };

  const exportSnapshot = () => {
    const text = [
      "LIQUIDITY → CONTROL · TREASURY SNAPSHOT",
      d.meta.disclaimer,
      `Scenario ${t.scenario} · Strategy ${rec.id}`,
      `Idle reduction ${formatPct(rec.idle_reduction)}`,
      `Financing savings ${formatNum(rec.financing_savings)}`,
      `Efficiency ${rec.efficiency}/100 (project-defined)`,
      ...d.findings,
      "Methodology: simulated Orion book, Jan 2024–Dec 2026.",
    ].join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "treasury-snapshot.txt";
    a.click();
  };

  const exportCsv = () => {
    const rows = (o.scorecard || []).map((r: any) => `${r.name},${r.idle},${r.financing_cost},${r.fx},${r.score}`);
    const csv = ["strategy,idle,financing,fx,score", ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "strategy-scorecard.csv";
    a.click();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Eyebrow>10 · Strategy lab</Eyebrow>
          <h1 className="font-display text-3xl">The treasury decision</h1>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={exportCsv} className="rounded-full border border-white/10 px-3 py-1 text-[11px] uppercase text-mute">
            CSV
          </button>
          <button type="button" onClick={exportSnapshot} className="rounded-full border border-white/10 px-3 py-1 text-[11px] uppercase text-mute">
            Snapshot
          </button>
        </div>
      </div>

      <Panel>
        <div className="text-[10px] uppercase tracking-[0.2em] text-cyan">Recommended strategy · simulated</div>
        <h2 className="font-display mt-2 text-3xl">{rec.name}</h2>
        <p className="mt-2 text-sm text-mute">{d.disclaimer}</p>
        <ul className="mt-4 grid gap-2 text-sm text-mute md:grid-cols-2">
          {rec.reasons.map((r: string) => (
            <li key={r}>→ {r}</li>
          ))}
        </ul>
        <div className="mt-6 grid gap-3 md:grid-cols-4">
          <Stat label="Idle cash reduction" value={formatPct(rec.idle_reduction)} hint="SIMULATED OPTIMIZATION RESULT" />
          <Stat label="Financing cost reduction" value={money(rec.financing_savings, d.meta.symbol, d.meta.unit)} />
          <Stat label="FX exposure change" value={formatPct(rec.fx_reduction)} />
          <Stat label="Liquidity efficiency" value={`${formatNum(rec.efficiency, 0)} / 100`} hint="Project-defined metric." />
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-display text-xl">Before</h2>
          <div className="mt-3 space-y-1 text-sm">
            <div>Idle {money(ba.before.idle, d.meta.symbol, d.meta.unit)}</div>
            <div>Borrowing {money(ba.before.borrowing, d.meta.symbol, d.meta.unit)}</div>
            <div>Investment income {money(ba.before.investment_income, d.meta.symbol, d.meta.unit)}</div>
            <div>FX {money(ba.before.fx, d.meta.symbol, d.meta.unit)}</div>
          </div>
        </Panel>
        <Panel>
          <h2 className="font-display text-xl">After · hybrid</h2>
          <div className="mt-3 space-y-1 text-sm">
            <div>Idle {money(ba.after.idle, d.meta.symbol, d.meta.unit)}</div>
            <div>Borrowing {money(ba.after.borrowing, d.meta.symbol, d.meta.unit)}</div>
            <div>Investment income {money(ba.after.investment_income, d.meta.symbol, d.meta.unit)}</div>
            <div>FX {money(ba.after.fx, d.meta.symbol, d.meta.unit)}</div>
          </div>
        </Panel>
      </div>

      <Panel>
        <h2 className="font-display text-xl">Score weights</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <SliderRow label="Liquidity" min={0} max={70} step={5} value={wL} onChange={setWL} suffix="%" />
          <SliderRow label="Cost" min={0} max={70} step={5} value={wC} onChange={setWC} suffix="%" />
          <SliderRow label="FX risk" min={0} max={70} step={5} value={wF} onChange={setWF} suffix="%" />
          <SliderRow label="Return" min={0} max={70} step={5} value={wR} onChange={setWR} suffix="%" />
        </div>
        <p className="mt-2 text-[11px] text-faint">Winner updates as weights move. Not an industry index.</p>
        {o.scorecard && (
          <Table
            columns={[
              { key: "name", label: "Strategy" },
              { key: "idle", label: "Idle", align: "right" },
              { key: "financing_cost", label: "Financing", align: "right" },
              { key: "fx", label: "FX", align: "right" },
              { key: "investment_income", label: "Income", align: "right" },
              { key: "complexity", label: "Complexity", align: "right" },
              { key: "score", label: "Score", align: "right" },
            ]}
            rows={o.scorecard.map((r: any) => ({
              name: r.name,
              idle: formatNum(r.idle),
              financing_cost: formatNum(r.financing_cost),
              fx: formatNum(r.fx),
              investment_income: formatNum(r.investment_income),
              complexity: r.complexity,
              score: r.score,
            }))}
          />
        )}
      </Panel>

      {o.waterfall && (
        <Panel>
          <h2 className="font-display text-xl">Financing cost waterfall</h2>
          <WaterfallChart
            data={o.waterfall.map((w: any, i: number) => ({
              label: w.label,
              value: w.value,
              type: i === 0 || i === o.waterfall.length - 1 ? "total" : "flow",
            }))}
          />
        </Panel>
      )}

      <Panel>
        <h2 className="font-display text-xl">What we found</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-mute">
          {d.findings.map((f: string) => (
            <li key={f}>{f}</li>
          ))}
        </ol>
      </Panel>

      <Panel>
        <h2 className="font-display text-xl">What could go wrong?</h2>
        <ul className="mt-3 space-y-2 text-sm text-mute">
          {d.what_could_go_wrong.map((f: string) => (
            <li key={f}>⚠ {f}</li>
          ))}
        </ul>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel>
          <h2 className="font-display text-xl">Treasury health</h2>
          {Object.entries(d.health).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between border-b border-white/5 py-2 text-sm">
              <span className="capitalize text-mute">{k}</span>
              <span>{"★".repeat(v as number)}{"☆".repeat(5 - (v as number))}</span>
            </div>
          ))}
          <p className="mt-2 text-[11px] text-faint">Visual summary only.</p>
        </Panel>
        <Panel>
          <h2 className="font-display text-xl">Decision rules</h2>
          <ul className="space-y-2 text-[13px] text-mute">
            {d.rules.map((r: any) => (
              <li key={r.id}>
                <span className="text-faint">IF</span> {r.if} <span className="text-faint">THEN</span> {r.then}
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      {matrix.data && (
        <Panel>
          <h2 className="font-display text-xl">Global cash-flow matrix</h2>
          <Table
            columns={[
              { key: "metric", label: "Metric" },
              ...((matrix.data as any).columns || []).map((c: string) => ({ key: c, label: c, align: "right" as const })),
            ]}
            rows={(matrix.data as any).rows.map((r: any) => {
              const row: Record<string, string | number> = { metric: r.metric };
              (matrix.data as any).columns.forEach((c: string) => (row[c] = formatNum(r[c])));
              return row;
            })}
          />
        </Panel>
      )}

      {conc.data && (
        <Panel>
          <h2 className="font-display text-xl">Cash vs revenue concentration</h2>
          <Bars
            data={(conc.data as any).series}
            x="country"
            series={[
              { key: "cash_share", color: "#22D3EE", name: "Cash share" },
              { key: "revenue_share", color: "#C084FC", name: "Revenue share" },
            ]}
          />
          <p className="text-[12px] text-mute">{(conc.data as any).risk}</p>
        </Panel>
      )}

      {sankey.data && (
        <Panel>
          <h2 className="font-display text-xl">Where did the cash go?</h2>
          <p className="mb-3 text-[12px] text-mute">Sankey-style flows from the simulated book. Click a flow in the table.</p>
          <Table
            columns={[
              { key: "source", label: "From" },
              { key: "target", label: "To" },
              { key: "value", label: "Amount", align: "right" },
            ]}
            rows={(sankey.data as any).links.map((l: any) => ({ source: l.source, target: l.target, value: formatNum(l.value) }))}
          />
        </Panel>
      )}

      {events.data && (
        <Panel>
          <h2 className="font-display text-xl">Cash-flow calendar · Sep 2026</h2>
          <div className="mt-3 grid grid-cols-7 gap-1 text-[10px]">
            {["M", "T", "W", "T", "F", "S", "S"].map((d0, i) => (
              <div key={i} className="text-center text-faint">
                {d0}
              </div>
            ))}
            {Array.from({ length: 30 }, (_, i) => {
              const day = i + 1;
              const date = `2026-09-${String(day).padStart(2, "0")}`;
              const ev = (events.data as any[]).filter((e) => e.date === date);
              return (
                <div key={day} className="min-h-[52px] border border-white/5 p-1" title={ev.map((e) => e.label).join(", ")}>
                  <div className="text-faint">{day}</div>
                  {ev.slice(0, 2).map((e, j) => (
                    <div key={j} className="truncate text-cyan">
                      {e.category}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      <Panel>
        <Eyebrow>Optional · You are the group treasurer</Eyebrow>
        <h2 className="font-display text-xl">₹100Cr excess cash. What do you do?</h2>
        <div className="mt-4 grid gap-2 md:grid-cols-4">
          {[
            { id: "idle", label: "A · Leave idle" },
            { id: "invest", label: "B · Invest it" },
            { id: "pool", label: "C · Pool it" },
            { id: "borrow", label: "D · Cut borrowing" },
          ].map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={async () => {
                setChoice(c.id);
                setGame(await api.game({ choice: c.id, amount: 100, reporting: t.reporting }));
              }}
              className={`border px-3 py-4 text-left text-sm ${choice === c.id ? "border-cyan" : "border-white/10"}`}
            >
              {c.label}
            </button>
          ))}
        </div>
        {game && (
          <div className="mt-4">
            <div className="font-display text-lg">{game.title}</div>
            <p className="text-sm text-mute">{game.scores.note}</p>
            <div className="mt-2 grid grid-cols-4 gap-2 text-[12px]">
              <div>Liquidity {game.scores.liquidity}</div>
              <div>Return {game.scores.return}</div>
              <div>Cost {game.scores.cost}</div>
              <div>FX {game.scores.fx}</div>
            </div>
            <p className="mt-2 text-[11px] text-faint">{game.disclaimer}</p>
          </div>
        )}
      </Panel>

      <Learn on={t.learning}>
        Hybrid pooling plus deploying a sleeve of surplus into short-term instruments is what produces the calculated idle-cash reduction in this book. Change the weights if you care more about FX than cost.
      </Learn>
    </div>
  );
}
