import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { Eyebrow, Panel } from "../components/ui/primitives";

export function Research() {
  const t = useTreasury();
  const [metric, setMetric] = useState("idle");
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const run = async () => {
    setBusy(true);
    try {
      setResult(
        await api.research({
          country: t.country,
          currency: t.reporting,
          scenario: t.scenario,
          strategy: t.strategy,
          metric,
        })
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="space-y-6">
      <Eyebrow>11 · Research mode</Eyebrow>
      <h1 className="font-display text-3xl">Build your treasury analysis</h1>
      <Panel>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="text-[12px] uppercase tracking-wider text-faint">
            Metric
            <select className="mt-1 block w-full bg-transparent text-ink" value={metric} onChange={(e) => setMetric(e.target.value)}>
              <option value="idle">Idle cash</option>
              <option value="cash">Closing cash</option>
              <option value="funding">Funding gap</option>
              <option value="fx">FX exposure</option>
            </select>
          </label>
          <div className="text-[12px] text-mute">
            Uses the top-bar country, currency, scenario and strategy. Write the question the way a treasurer would.
          </div>
          <button type="button" onClick={run} className="self-end rounded-full bg-cyan px-4 py-2 text-sm font-semibold text-bg">
            {busy ? "Running…" : "Generate"}
          </button>
        </div>
      </Panel>
      {result && (
        <div className="grid gap-3 md:grid-cols-2">
          {[
            ["Question", result.question],
            ["Data", result.data],
            ["Method", result.method],
            ["Result", money(result.result, result.meta.symbol, result.meta.unit)],
            ["Interpretation", result.interpretation],
            ["Limitations", result.limitations],
          ].map(([k, v]) => (
            <Panel key={k}>
              <div className="text-[10px] uppercase tracking-[0.18em] text-faint">{k}</div>
              <p className="mt-2 text-sm text-mute">{v}</p>
            </Panel>
          ))}
        </div>
      )}
    </div>
  );
}

export function Methodology() {
  const t = useTreasury();
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api.methodology().then(setData);
  }, []);
  if (!data) return <div className="text-mute">Loading method notes…</div>;
  return (
    <div className="space-y-6">
      <Eyebrow>12 · Methodology</Eyebrow>
      <h1 className="font-display text-3xl">{data.title}</h1>
      <p className="text-sm text-pink">{data.disclaimer}</p>
      <Panel>
        <p className="text-sm leading-relaxed text-mute">{data.company}</p>
        <dl className="mt-4 grid gap-3 text-sm md:grid-cols-2">
          <div>
            <dt className="text-faint">Period</dt>
            <dd>{data.period}</dd>
          </div>
          <div>
            <dt className="text-faint">Generation</dt>
            <dd>{data.generation}</dd>
          </div>
          <div>
            <dt className="text-faint">FX</dt>
            <dd>{data.fx}</dd>
          </div>
          <div>
            <dt className="text-faint">Rates</dt>
            <dd>{data.rates}</dd>
          </div>
          <div>
            <dt className="text-faint">Working capital</dt>
            <dd>{data.working_capital}</dd>
          </div>
          <div>
            <dt className="text-faint">Pooling</dt>
            <dd>{data.pooling}</dd>
          </div>
          <div>
            <dt className="text-faint">Optimization</dt>
            <dd>{data.optimization}</dd>
          </div>
          <div>
            <dt className="text-faint">The ~12%</dt>
            <dd>{data.twelve_pct}</dd>
          </div>
        </dl>
      </Panel>
      <Panel>
        <h2 className="font-display text-xl">Formulas</h2>
        <ul className="mt-3 space-y-2 font-mono text-[12px] text-mute">
          {Object.entries(data.formulas).map(([k, v]) => (
            <li key={k}>
              <span className="text-cyan">{k}</span> · {String(v)}
            </li>
          ))}
        </ul>
      </Panel>
      <Panel>
        <h2 className="font-display text-xl">Model limitations</h2>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-mute">
          {data.limitations.map((l: string) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Panel>
      {t.learning && (
        <Panel>
          <p className="text-sm text-mute">
            Learning mode is on. Every lab screen adds definitions, the formula, a small example and how to read the number. Analyst
            mode hides that copy.
          </p>
        </Panel>
      )}
    </div>
  );
}
