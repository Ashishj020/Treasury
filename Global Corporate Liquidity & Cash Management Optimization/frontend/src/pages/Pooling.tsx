import { useState } from "react";
import { api } from "../lib/api";
import { formatNum, formatPct, money } from "../lib/format";
import { useTreasury } from "../lib/store";
import { useApi } from "../lib/useApi";
import { ErrorState, Eyebrow, Learn, Panel, Segment, Skeleton, SliderRow, Stat, Table } from "../components/ui/primitives";

const STRATS = [
  { id: "none", label: "None" },
  { id: "physical", label: "Physical" },
  { id: "notional", label: "Notional" },
  { id: "hybrid", label: "Hybrid" },
] as const;

export function Pooling() {
  const t = useTreasury();
  const [members, setMembers] = useState(["IN", "US", "UK", "SG"]);
  const [transfer, setTransfer] = useState(5);
  const [invest, setInvest] = useState(22);
  const [borrow, setBorrow] = useState(2);
  const [buffer, setBuffer] = useState(1);
  const extra = {
    members: members.join(","),
    transfer_threshold: transfer,
    investment_threshold: invest,
    borrowing_threshold: borrow,
    min_buffer_mult: buffer,
  };
  const { data, error, loading } = useApi(
    () => api.pooling({ reporting: t.reporting, scenario: t.scenario, strategy: t.strategy, country: t.country }, extra),
    [t.reporting, t.scenario, t.strategy, members, transfer, invest, borrow, buffer]
  );
  if (loading) return <Skeleton className="h-[60vh]" />;
  if (error || !data) return <ErrorState message={error || ""} />;
  const d = data as any;
  const meta = d.meta;
  const toggle = (c: string) => setMembers((m) => (m.includes(c) ? m.filter((x) => x !== c) : [...m, c]));

  return (
    <div className="space-y-6">
      <Eyebrow>05 · Cash pooling lab</Eyebrow>
      <h1 className="font-display text-3xl">Would pooling solve the funding gap?</h1>
      <p className="max-w-2xl text-sm text-mute">{d.feasibility}</p>

      <div className="flex flex-wrap gap-2">
        <Segment value={t.strategy} onChange={t.setStrategy} options={[...STRATS]} />
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Panel>
          <Stat label="Idle cash" value={money(d.totals.idle, meta.symbol, meta.unit)} hint={`Baseline ${formatNum(d.baseline.idle)}`} />
        </Panel>
        <Panel>
          <Stat label="Funding need" value={money(d.totals.funding, meta.symbol, meta.unit)} />
        </Panel>
        <Panel>
          <Stat label="Interest income" value={money(d.totals.interest_income, meta.symbol, meta.unit)} tone="pos" />
        </Panel>
        <Panel>
          <Stat label="Borrowing cost" value={money(d.totals.interest_expense, meta.symbol, meta.unit)} tone="neg" />
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <Panel>
          <h2 className="font-display text-xl">Simulator</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {["IN", "US", "UK", "SG"].map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => toggle(c)}
                className={`rounded-full border px-3 py-1 text-[12px] ${members.includes(c) ? "border-cyan text-cyan" : "border-white/10 text-mute"}`}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="mt-4 space-y-3">
            <SliderRow label="Min cash buffer ×" min={0.8} max={1.3} step={0.02} value={buffer} onChange={setBuffer} />
            <SliderRow label="Transfer threshold" min={0} max={20} step={0.5} value={transfer} onChange={setTransfer} />
            <SliderRow label="Investment threshold" min={5} max={40} step={0.5} value={invest} onChange={setInvest} />
            <SliderRow label="Borrowing threshold" min={0} max={10} step={0.5} value={borrow} onChange={setBorrow} />
          </div>
          <p className="mt-4 text-[13px] text-mute">{d.tradeoff}</p>
        </Panel>
        <Panel>
          <h2 className="font-display text-xl">Sweeps</h2>
          {d.transfers.length === 0 ? (
            <p className="mt-3 text-sm text-mute">No physical sweep in this structure. Notional keeps cash in-country.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {d.transfers.map((tr: any, i: number) => (
                <li key={i} className="flex items-center justify-between border border-white/10 px-3 py-2 text-sm">
                  <span>
                    {tr.from} → {tr.to}
                    <span className="block text-[11px] text-mute">{tr.note}</span>
                  </span>
                  <span className="num text-cyan">{money(tr.amount_inr, "₹", "Cr")}</span>
                </li>
              ))}
            </ul>
          )}
          <Learn on={t.learning}>{d.explanations[t.strategy]}</Learn>
        </Panel>
      </div>

      <Panel>
        <h2 className="font-display text-xl">Physical vs notional</h2>
        <Table
          columns={[
            { key: "k", label: "" },
            { key: "p", label: "Physical" },
            { key: "n", label: "Notional" },
          ]}
          rows={[
            { k: "Cash movement", p: "Swept to header", n: "Stays local" },
            { k: "Idle cash", p: "Falls as surplus is redeployed", n: "Barely moves" },
            { k: "Interest", p: "Header earns / deficit entities borrow internally", n: "Bank nets interest" },
            { k: "FX", p: "Conversion on each sweep", n: "Limited" },
            { k: "Complexity", p: "High — legal, tax, ops", n: "High — bank mandate, jurisdiction" },
            { k: "Regulation", p: "Capital controls can block sweeps", n: "Not offered in every market" },
          ]}
        />
      </Panel>

      <Panel>
        <h2 className="font-display text-xl">Country positions after structure</h2>
        <Table
          columns={[
            { key: "country", label: "Country" },
            { key: "closing", label: "Cash", align: "right" },
            { key: "idle", label: "Idle", align: "right" },
            { key: "funding", label: "Funding", align: "right" },
            { key: "status", label: "Status" },
          ]}
          rows={(d.positions || []).map((p: any) => ({
            country: p.country,
            closing: formatNum(p.closing),
            idle: formatNum(p.idle),
            funding: formatNum(p.funding),
            status: p.status,
          }))}
        />
      </Panel>
    </div>
  );
}
