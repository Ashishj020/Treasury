import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/navigation/AppShell";
import { Landing } from "./pages/Landing";

const Overview = lazy(() => import("./pages/Overview").then((m) => ({ default: m.Overview })));
const CashFlows = lazy(() => import("./pages/CashFlows").then((m) => ({ default: m.CashFlows })));
const Liquidity = lazy(() => import("./pages/Liquidity").then((m) => ({ default: m.Liquidity })));
const WorkingCapital = lazy(() => import("./pages/WorkingCapital").then((m) => ({ default: m.WorkingCapital })));
const Pooling = lazy(() => import("./pages/Pooling").then((m) => ({ default: m.Pooling })));
const Investments = lazy(() => import("./pages/InvestBorrow").then((m) => ({ default: m.Investments })));
const Borrowing = lazy(() => import("./pages/InvestBorrow").then((m) => ({ default: m.Borrowing })));
const FX = lazy(() => import("./pages/FX").then((m) => ({ default: m.FX })));
const Scenarios = lazy(() => import("./pages/Scenarios").then((m) => ({ default: m.Scenarios })));
const Strategy = lazy(() => import("./pages/Strategy").then((m) => ({ default: m.Strategy })));
const Research = lazy(() => import("./pages/Research").then((m) => ({ default: m.Research })));
const Methodology = lazy(() => import("./pages/Research").then((m) => ({ default: m.Methodology })));

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <Suspense fallback={<div className="animate-pulse text-sm text-mute">Retrieving the simulated book…</div>}>{children}</Suspense>
    </AppShell>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/overview" element={<Screen><Overview /></Screen>} />
        <Route path="/cash-flows" element={<Screen><CashFlows /></Screen>} />
        <Route path="/liquidity" element={<Screen><Liquidity /></Screen>} />
        <Route path="/working-capital" element={<Screen><WorkingCapital /></Screen>} />
        <Route path="/pooling" element={<Screen><Pooling /></Screen>} />
        <Route path="/investments" element={<Screen><Investments /></Screen>} />
        <Route path="/borrowing" element={<Screen><Borrowing /></Screen>} />
        <Route path="/fx" element={<Screen><FX /></Screen>} />
        <Route path="/scenarios" element={<Screen><Scenarios /></Screen>} />
        <Route path="/strategy" element={<Screen><Strategy /></Screen>} />
        <Route path="/research" element={<Screen><Research /></Screen>} />
        <Route path="/methodology" element={<Screen><Methodology /></Screen>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
