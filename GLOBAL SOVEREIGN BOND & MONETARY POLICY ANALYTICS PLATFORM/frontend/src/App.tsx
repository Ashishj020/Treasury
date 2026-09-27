import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { UIProvider } from "./lib/store";
import { AppShell } from "./components/layout/AppShell";
import Landing from "./pages/Landing";
import { Skeleton } from "./components/ui/Card";

const Overview = lazy(() => import("./pages/Overview"));
const Policy = lazy(() => import("./pages/Policy"));
const Curves = lazy(() => import("./pages/Curves"));
const Cross = lazy(() => import("./pages/Cross"));
const Events = lazy(() => import("./pages/Events"));
const Returns = lazy(() => import("./pages/Returns"));
const Risk = lazy(() => import("./pages/Risk"));
const Macro = lazy(() => import("./pages/Macro"));
const Scenario = lazy(() => import("./pages/Scenario"));
const Notes = lazy(() => import("./pages/Notes"));
const Methodology = lazy(() => import("./pages/Methodology"));
const Sources = lazy(() => import("./pages/Sources"));

function Lab({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

export default function App() {
  return (
    <UIProvider>
      <BrowserRouter>
        <Suspense fallback={<div className="bg-lab min-h-screen p-10"><Skeleton className="h-40" /></div>}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/lab" element={<Navigate to="/lab/overview" replace />} />
            <Route path="/lab/overview" element={<Lab><Overview /></Lab>} />
            <Route path="/lab/policy" element={<Lab><Policy /></Lab>} />
            <Route path="/lab/curves" element={<Lab><Curves /></Lab>} />
            <Route path="/lab/cross" element={<Lab><Cross /></Lab>} />
            <Route path="/lab/events" element={<Lab><Events /></Lab>} />
            <Route path="/lab/returns" element={<Lab><Returns /></Lab>} />
            <Route path="/lab/risk" element={<Lab><Risk /></Lab>} />
            <Route path="/lab/macro" element={<Lab><Macro /></Lab>} />
            <Route path="/lab/scenario" element={<Lab><Scenario /></Lab>} />
            <Route path="/lab/notes" element={<Lab><Notes /></Lab>} />
            <Route path="/lab/methodology" element={<Lab><Methodology /></Lab>} />
            <Route path="/lab/sources" element={<Lab><Sources /></Lab>} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </UIProvider>
  );
}
