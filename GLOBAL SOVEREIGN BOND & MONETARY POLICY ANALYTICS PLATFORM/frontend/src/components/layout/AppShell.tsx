import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  BookOpen,
  Database,
  GitCompare,
  Landmark,
  LineChart,
  Menu,
  Search,
  Sigma,
  Spline,
  Timer,
  Waves,
  X,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useUI } from "../../lib/store";
import { MARKETS, MARKET_META } from "../../lib/format";
import { CommandBar } from "./CommandBar";
import { api } from "../../lib/api";

const NAV = [
  { to: "/lab/overview", label: "Overview", icon: Activity, n: "01" },
  { to: "/lab/policy", label: "Monetary Policy", icon: Landmark, n: "02" },
  { to: "/lab/curves", label: "Yield Curves", icon: Spline, n: "03" },
  { to: "/lab/cross", label: "Cross-Market", icon: GitCompare, n: "04" },
  { to: "/lab/events", label: "Event Study", icon: Timer, n: "05" },
  { to: "/lab/returns", label: "Bond Returns", icon: LineChart, n: "06" },
  { to: "/lab/risk", label: "Risk & Vol", icon: Waves, n: "07" },
  { to: "/lab/macro", label: "Macro Drivers", icon: Sigma, n: "08" },
  { to: "/lab/scenario", label: "Scenario Lab", icon: Activity, n: "09" },
  { to: "/lab/notes", label: "Research Notes", icon: BookOpen, n: "10" },
  { to: "/lab/methodology", label: "Methodology", icon: BookOpen, n: "11" },
  { to: "/lab/sources", label: "Data Sources", icon: Database, n: "12" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { market, setMarket, range, setRange, frequency, setFrequency, mode, setMode, setCommandOpen } = useUI();
  const [open, setOpen] = useState(false);
  const [demo, setDemo] = useState(true);
  const loc = useLocation();
  const nav = useNavigate();

  useEffect(() => {
    api.status().then((s) => setDemo(s.demo_mode)).catch(() => setDemo(true));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setCommandOpen]);

  useEffect(() => setOpen(false), [loc.pathname]);

  return (
    <div className="bg-lab grain min-h-screen text-mist-50">
      <div className="relative z-10 flex min-h-screen">
        <aside className="hidden lg:flex w-[232px] shrink-0 flex-col border-r border-white/[0.06] bg-ink-1/80 backdrop-blur-xl">
          <button onClick={() => nav("/")} className="px-5 pt-6 pb-4 text-left">
            <div className="font-serif text-lg tracking-tight">POLICY → YIELDS</div>
            <div className="kicker mt-1">Sovereign lab</div>
          </button>
          <nav className="flex-1 px-2 pb-4 space-y-0.5 overflow-y-auto">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-xl px-3 py-2 text-[13px] transition ${
                    isActive ? "bg-white/[0.06] text-cyan" : "text-mist-400 hover:text-mist-50 hover:bg-white/[0.03]"
                  }`
                }
              >
                <span className="num text-[10px] text-mist-600 w-5">{n.n}</span>
                <n.icon size={14} />
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="p-4 text-[10px] text-mist-600 leading-relaxed">
            Educational research project — not investment advice.
          </div>
        </aside>

        <div className="flex-1 min-w-0 flex flex-col">
          <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-ink-0/75 backdrop-blur-xl">
            <div className="flex items-center gap-3 px-4 py-3">
              <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
                <Menu size={18} />
              </button>
              <div className="hidden md:block">
                <div className="font-serif text-base">Global Sovereign Bond Market Lab</div>
                <div className="text-[11px] text-mist-400">How central-bank decisions travel through fixed-income markets.</div>
              </div>
              <div className="ml-auto flex flex-wrap items-center gap-2">
                <span className={`num text-[10px] px-2 py-1 rounded-full border ${demo ? "border-amber-400/40 text-amber-200" : "border-emerald/40 text-emerald"}`}>
                  ● {demo ? "DEMO MODE" : "LIVE DATA"}
                </span>
                {MARKETS.map((m) => (
                  <button
                    key={m}
                    onClick={() => setMarket(m)}
                    className={`num text-[11px] px-2 py-1 rounded-full border ${
                      market === m ? "border-cyan/50 text-cyan" : "border-white/10 text-mist-400"
                    }`}
                  >
                    {MARKET_META[m].short}
                  </button>
                ))}
                <select
                  value={range}
                  onChange={(e) => setRange(e.target.value)}
                  className="bg-ink-2 border border-white/10 rounded-lg text-[11px] px-2 py-1 num"
                >
                  {["1Y", "3Y", "5Y", "10Y", "MAX"].map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
                <select
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  className="bg-ink-2 border border-white/10 rounded-lg text-[11px] px-2 py-1 num"
                >
                  {["daily", "weekly", "monthly"].map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
                <button
                  onClick={() => setMode(mode === "learn" ? "analyst" : "learn")}
                  className="text-[11px] px-2 py-1 rounded-lg border border-white/10 text-mist-400"
                >
                  {mode === "learn" ? "LEARNING MODE" : "ANALYST MODE"}
                </button>
                <button onClick={() => setCommandOpen(true)} className="hidden sm:flex items-center gap-2 text-[11px] px-2 py-1 rounded-lg border border-white/10 text-mist-400">
                  <Search size={12} /> Search ⌘K
                </button>
              </div>
            </div>
          </header>
          <main className="flex-1 p-4 md:p-6">{children}</main>
          <footer className="px-6 py-4 text-[11px] text-mist-600 border-t border-white/[0.06] flex flex-wrap gap-4">
            <span className="font-serif text-mist-400">POLICY → YIELDS</span>
            <span>Educational research project — not investment advice.</span>
            <a className="hover:text-cyan" href="/lab/sources">
              Data sources
            </a>
            <a className="hover:text-cyan" href="/lab/methodology">
              Methodology
            </a>
            <span>GitHub: your-repo</span>
          </footer>
        </div>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 lg:hidden bg-black/60" onClick={() => setOpen(false)}>
          <div className="w-72 h-full bg-ink-1 p-4" onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setOpen(false)} className="mb-4">
              <X size={16} />
            </button>
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} className="flex items-center gap-2 py-2 text-sm text-mist-200">
                {n.label}
              </NavLink>
            ))}
          </div>
        </div>
      )}

      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 border-t border-white/10 bg-ink-1/95 backdrop-blur-xl flex justify-around py-2 text-[10px] text-mist-400">
        {NAV.slice(0, 5).map((n) => (
          <NavLink key={n.to} to={n.to} className={({ isActive }) => (isActive ? "text-cyan" : "")}>
            <div className="flex flex-col items-center gap-1">
              <n.icon size={14} />
              {n.label.split(" ")[0]}
            </div>
          </NavLink>
        ))}
      </nav>
      <CommandBar />
    </div>
  );
}
