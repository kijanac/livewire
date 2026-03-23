import { useState, useEffect, useMemo, lazy, Suspense } from "react";
import { triggerIngest } from "./api";
import { Button } from "@/components/ui/button";

const Dashboard = lazy(() => import("./components/Dashboard"));
const CollectionView = lazy(() => import("./components/CollectionView"));
const RadarView = lazy(() => import("./components/RadarView"));

type Route =
  | { page: "dashboard" }
  | { page: "collection"; slug: string }
  | { page: "radar" };

function useHashRoute(): Route {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const collectionMatch = hash.match(/^#\/collection\/(.+)$/);
  if (collectionMatch) return { page: "collection", slug: collectionMatch[1] };
  if (hash === "#/dashboard") return { page: "dashboard" };
  return { page: "radar" };
}

function App() {
  const route = useHashRoute();
  const collectionName = useMemo(() => {
    if (route.page !== "collection") return null;
    try {
      const stubs = JSON.parse(localStorage.getItem("bill_tracker_collections") || "[]");
      return stubs.find((s: { slug: string }) => s.slug === route.slug)?.name ?? null;
    } catch {
      return null;
    }
  }, [route]);

  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await triggerIngest();
      setSyncResult(
        `+${result.bills_added} new bills, ${result.bills_updated} updated`
      );
      setRefreshKey((k) => k + 1);
    } catch {
      setSyncResult("Refresh failed. Try again.");
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncResult(null), 5000);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b-2 border-primary bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-6">
              <a href="#" className="flex items-center gap-2.5 group">
                <div className="w-7 h-7 bg-primary flex items-center justify-center" aria-hidden="true">
                  <svg className="w-4 h-4 text-primary-foreground" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                    <path d="M3 8h10M8 3l5 5-5 5" />
                  </svg>
                </div>
                <span
                  className="text-xl font-black tracking-tight uppercase text-foreground font-[var(--font-heading)]"
                  style={{ fontVariationSettings: "'opsz' 72, 'WONK' 1" }}
                >
                  Livewire
                </span>
              </a>

              <nav className="flex items-center gap-0.5 border-l-2 border-border pl-4">
                <a
                  href="#"
                  className={`px-3 py-1 text-sm font-semibold uppercase tracking-wide transition-colors ${
                    route.page === "radar"
                      ? "text-primary border-b-2 border-primary -mb-px"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Radar
                </a>
                <a
                  href="#/dashboard"
                  className={`px-3 py-1 text-sm font-semibold uppercase tracking-wide transition-colors ${
                    route.page === "dashboard"
                      ? "text-primary border-b-2 border-primary -mb-px"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Dashboard
                </a>
              </nav>

              {route.page === "collection" && (
                <span className="text-sm text-muted-foreground font-semibold uppercase tracking-wide">
                  / {collectionName || "Collection"}
                </span>
              )}
            </div>

            <div className="flex items-center gap-3">
              {syncResult && (
                <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                  {syncResult}
                </span>
              )}
              {route.page === "dashboard" && (
                <Button
                  onClick={handleSync}
                  disabled={syncing}
                  variant="outline"
                  size="sm"
                  className="font-[var(--font-mono)] text-xs uppercase tracking-wider"
                >
                  {syncing ? (
                    <>
                      <svg
                        className="animate-spin motion-reduce:animate-none h-3.5 w-3.5"
                        viewBox="0 0 24 24"
                        fill="none"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      Refreshing
                    </>
                  ) : (
                    "Refresh Data"
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      <Suspense fallback={
        <div className="flex items-center justify-center py-24">
          <svg className="animate-spin motion-reduce:animate-none h-6 w-6 text-primary" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      }>
        {route.page === "radar" ? (
          <RadarView />
        ) : route.page === "collection" ? (
          <CollectionView slug={route.slug} />
        ) : (
          <Dashboard refreshKey={refreshKey} />
        )}
      </Suspense>
    </div>
  );
}

export default App;
