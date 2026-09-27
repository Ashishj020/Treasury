import { useMemo, useState } from "react";
import { GLOSSARY } from "../lib/glossary";
import { Kicker, Panel } from "../components/ui/Card";
import { MARKETS } from "../lib/format";
import { useUI } from "../lib/store";

export default function Notes() {
  const { market, range } = useUI();
  const [country, setCountry] = useState<string>(market);
  const [period, setPeriod] = useState(range);
  const [event, setEvent] = useState("Fed hiking 2022–23");
  const [maturity, setMaturity] = useState("10Y");
  const [metric, setMetric] = useState("Yield change (bp)");
  const [q, setQ] = useState("");

  const note = useMemo(
    () => ({
      question: `Within this DEMO sample, how did ${country} ${maturity} ${metric.toLowerCase()} behave around “${event}” over ${period}?`,
      data: `Simulated ${country} par yields and policy path, ${period} window, ${maturity} tenor. Labelled DEMO — not official prints.`,
      method: "Descriptive comparison of sample statistics. No causal identification. See Methodology for formulas.",
      result: "Open Overview / Event Study / Curve Lab with the same filters and copy the calculated numbers. This notebook does not invent a result.",
      interpretation:
        "Any pattern is an observed association in a historically inspired sandbox. Alternative explanations (global inflation, fiscal, FX) are not controlled for here.",
      limitations: "Synthetic data; small event counts; classical standard errors; Nelson-Siegel is a smoother not a no-arbitrage model.",
    }),
    [country, period, event, maturity, metric],
  );

  const terms = GLOSSARY.filter((t) => t.term.toLowerCase().includes(q.toLowerCase()));

  function download() {
    const text = `POLICY → YIELDS — research snapshot
${note.question}

QUESTION
${note.question}

DATA
${note.data}

METHOD
${note.method}

RESULT
${note.result}

INTERPRETATION
${note.interpretation}

LIMITATIONS
${note.limitations}

Educational research project — not investment advice.
`;
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "policy-yields-research-snapshot.txt";
    a.click();
  }

  function csv() {
    const rows = [["term", "definition"], ...GLOSSARY.map((t) => [t.term, t.definition])];
    const blob = new Blob([rows.map((r) => r.map((x) => `"${x.replaceAll('"', '""')}"`).join(",")).join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "policy-yields-glossary.csv";
    a.click();
  }

  return (
    <div className="space-y-6">
      <div>
        <Kicker>10 — Research notes</Kicker>
        <h1 className="font-serif text-3xl md:text-4xl mt-1">Build your analysis</h1>
      </div>
      <div className="grid md:grid-cols-5 gap-2">
        <Field label="Country" value={country} set={setCountry} opts={[...MARKETS]} />
        <Field label="Period" value={period} set={setPeriod} opts={["1Y", "3Y", "5Y", "10Y", "MAX"]} />
        <Field label="Policy event" value={event} set={setEvent} opts={["Fed hiking 2022–23", "COVID easing", "QT", "Gilt stress 2022", "2024 cuts"]} />
        <Field label="Maturity" value={maturity} set={setMaturity} opts={["2Y", "5Y", "10Y", "30Y"]} />
        <Field label="Metric" value={metric} set={setMetric} opts={["Yield change (bp)", "2s10s", "Total return", "Realised vol"]} />
      </div>
      <div className="space-y-3">
        {Object.entries({ QUESTION: note.question, DATA: note.data, METHOD: note.method, RESULT: note.result, INTERPRETATION: note.interpretation, LIMITATIONS: note.limitations }).map(
          ([k, v]) => (
            <Panel key={k}>
              <div className="kicker">{k}</div>
              <p className="text-sm mt-2 text-mist-200">{v}</p>
            </Panel>
          ),
        )}
      </div>
      <div className="flex gap-2">
        <button onClick={download} className="px-3 py-2 rounded-full bg-cyan text-ink-0 text-xs">
          Download research snapshot
        </button>
        <button onClick={csv} className="px-3 py-2 rounded-full border border-white/15 text-xs">
          Export glossary CSV
        </button>
      </div>

      <div>
        <Kicker>Glossary</Kicker>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter terms…"
          className="mt-2 w-full bg-ink-2 border border-white/10 rounded-xl px-3 py-2 text-sm"
        />
        <div className="mt-3 grid md:grid-cols-2 gap-3">
          {terms.map((t) => (
            <div key={t.term} className="panel rounded-2xl p-4">
              <div className="font-serif text-lg">{t.term}</div>
              <p className="text-sm text-mist-300 mt-1">{t.definition}</p>
              <p className="text-xs text-mist-500 mt-2">
                <span className="text-cyan">WHY. </span>
                {t.why}
              </p>
              {t.formula && <p className="num text-[11px] text-orchid mt-2">{t.formula}</p>}
              <p className="text-xs text-mist-500 mt-2">
                <span className="text-emerald">EXAMPLE. </span>
                {t.example}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, set, opts }: { label: string; value: string; set: (s: string) => void; opts: string[] }) {
  return (
    <label className="text-[11px] text-mist-400">
      {label}
      <select value={value} onChange={(e) => set(e.target.value)} className="mt-1 w-full bg-ink-2 border border-white/10 rounded-lg text-xs px-2 py-2">
        {opts.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}
