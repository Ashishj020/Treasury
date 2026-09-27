import { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import { COUNTRIES, NAV } from "../../lib/format";
import { useTreasury } from "../../lib/store";
import { Segment } from "../ui/primitives";

const COMMANDS = [
  ...NAV.map((n) => ({ id: n.to, label: n.label, hint: "Go", to: n.to })),
  { id: "idle", label: "India idle cash", hint: "Overview", to: "/overview" },
  { id: "fx", label: "USD/INR exposure", hint: "FX", to: "/fx" },
  { id: "sg", label: "Singapore funding gap", hint: "Liquidity", to: "/liquidity" },
  { id: "pool", label: "cash pooling", hint: "Pooling", to: "/pooling" },
  { id: "wc", label: "working capital", hint: "WC", to: "/working-capital" },
  { id: "stress", label: "stressed scenario", hint: "Scenarios", to: "/scenarios" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const nav = useNavigate();
  const t = useTreasury();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [mobile, setMobile] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = useMemo(() => {
    const s = q.toLowerCase();
    return COMMANDS.filter((c) => c.label.toLowerCase().includes(s));
  }, [q]);

  return (
    <div className="mesh min-h-screen">
      <div className="grid-bg min-h-screen">
        <div className="noise" />
        <div className="flex min-h-screen">
          <aside className="hidden w-[232px] shrink-0 border-r border-white/[0.06] lg:block">
            <div className="sticky top-0 flex h-screen flex-col p-5">
              <NavLink to="/" className="mb-8">
                <div className="font-display text-[13px] tracking-[0.28em] text-cyan">LIQUIDITY → CONTROL</div>
                <div className="mt-1 text-[10px] uppercase tracking-[0.18em] text-faint">Orion Global · London HQ</div>
              </NavLink>
              <nav className="flex-1 space-y-0.5 overflow-y-auto">
                {NAV.map((n) => (
                  <NavLink
                    key={n.to}
                    to={n.to}
                    className={({ isActive }) =>
                      `flex items-baseline gap-3 rounded-md px-2 py-2 text-[13px] transition ${
                        isActive ? "bg-white/[0.05] text-ink" : "text-mute hover:text-ink"
                      }`
                    }
                  >
                    <span className="num text-[10px] text-faint">{n.id}</span>
                    {n.label}
                  </NavLink>
                ))}
              </nav>
              <div className="mt-4 text-[10px] uppercase tracking-[0.16em] text-faint">Simulated corporate treasury data</div>
            </div>
          </aside>

          <div className="flex min-w-0 flex-1 flex-col">
            <header className="glass sticky top-0 z-20 flex flex-wrap items-center gap-3 border-b border-white/[0.06] px-4 py-3 lg:px-6">
              <button type="button" className="lg:hidden text-mute" onClick={() => setMobile((v) => !v)} aria-label="Menu">
                ☰
              </button>
              <div className="hidden font-display text-sm text-ink md:block">GLOBAL TREASURY COMMAND CENTER</div>
              <div className="ml-auto flex flex-wrap items-center gap-2">
                <select
                  className="bg-transparent text-[12px] text-mute"
                  value={t.country}
                  onChange={(e) => t.setCountry(e.target.value as never)}
                  aria-label="Country"
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <Segment
                  value={t.reporting}
                  onChange={t.setReporting}
                  options={[
                    { id: "INR", label: "INR" },
                    { id: "USD", label: "USD" },
                    { id: "GBP", label: "GBP" },
                    { id: "SGD", label: "SGD" },
                  ]}
                />
                <select
                  className="bg-transparent text-[12px] text-mute"
                  value={t.scenario}
                  onChange={(e) => t.setScenario(e.target.value as never)}
                  aria-label="Scenario"
                >
                  <option value="base">Base</option>
                  <option value="optimistic">Optimistic</option>
                  <option value="stressed">Stressed</option>
                </select>
                <select
                  className="bg-transparent text-[12px] text-mute"
                  value={t.strategy}
                  onChange={(e) => t.setStrategy(e.target.value as never)}
                  aria-label="Strategy"
                >
                  <option value="none">No pooling</option>
                  <option value="physical">Physical</option>
                  <option value="notional">Notional</option>
                  <option value="hybrid">Hybrid</option>
                </select>
                <button
                  type="button"
                  onClick={() => t.setLearning(!t.learning)}
                  className={`rounded-full border px-3 py-1 text-[11px] uppercase tracking-wider ${
                    t.learning ? "border-cyan text-cyan" : "border-white/10 text-mute"
                  }`}
                >
                  {t.learning ? "Learning" : "Analyst"}
                </button>
                <button
                  type="button"
                  onClick={() => setOpen(true)}
                  className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-[11px] text-mute"
                >
                  <Search size={12} /> Search ⌘K
                </button>
              </div>
            </header>

            {mobile && (
              <div className="border-b border-white/10 p-3 lg:hidden">
                {NAV.map((n) => (
                  <NavLink key={n.to} to={n.to} onClick={() => setMobile(false)} className="block py-2 text-sm text-mute">
                    {n.id} {n.label}
                  </NavLink>
                ))}
              </div>
            )}

            <main className="relative z-10 flex-1 px-4 py-6 lg:px-8">{children}</main>
            <footer className="px-4 py-4 text-[10px] uppercase tracking-[0.16em] text-faint lg:px-8">
              Orion Global Industries · fictional book · {loc.pathname} · as-of Sep 2026
            </footer>
          </div>
        </div>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-[12vh] backdrop-blur-sm" onClick={() => setOpen(false)}>
          <div className="glass w-full max-w-lg rounded-2xl p-2" onClick={(e) => e.stopPropagation()}>
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search treasury data…"
              className="w-full bg-transparent px-4 py-3 text-sm outline-none"
            />
            <div className="max-h-80 overflow-y-auto">
              {filtered.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="flex w-full items-center justify-between px-4 py-2 text-left text-sm text-mute hover:bg-white/[0.04] hover:text-ink"
                  onClick={() => {
                    nav(c.to);
                    setOpen(false);
                    setQ("");
                  }}
                >
                  {c.label}
                  <span className="text-[10px] uppercase text-faint">{c.hint}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
