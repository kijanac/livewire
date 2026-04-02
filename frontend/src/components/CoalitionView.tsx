import { useState, useEffect, useCallback } from "react";
import { fetchCoalitions } from "../api";
import type { CoalitionsResponse, TopicCoalition, CityAlignment } from "../types";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MOMENTUM_CONFIG = {
  advancing: { label: "Advancing", color: "bg-green-500", textColor: "text-green-600 dark:text-green-400" },
  stalled: { label: "Stalled", color: "bg-red-500", textColor: "text-red-600 dark:text-red-400" },
  stable: { label: "Stable", color: "bg-amber-400", textColor: "text-amber-600 dark:text-amber-400" },
  mixed: { label: "Mixed", color: "bg-muted-foreground/40", textColor: "text-muted-foreground" },
} as const;

function MomentumBadge({ momentum }: { momentum: string }) {
  const config = MOMENTUM_CONFIG[momentum as keyof typeof MOMENTUM_CONFIG] ?? MOMENTUM_CONFIG.stable;
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs font-medium", config.textColor)}>
      <span className={cn("w-2 h-2 rounded-full", config.color)} />
      {config.label}
    </span>
  );
}

function CityRow({ city }: { city: CityAlignment }) {
  const total = city.passed + city.failed + city.pending;
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-sm text-foreground truncate">{city.city_name}</span>
        <MomentumBadge momentum={city.momentum} />
      </div>
      <div className="flex items-center gap-2 text-xs font-[var(--font-mono)] text-muted-foreground flex-shrink-0">
        {city.passed > 0 && <span className="text-green-600 dark:text-green-400">{city.passed}P</span>}
        {city.failed > 0 && <span className="text-red-600 dark:text-red-400">{city.failed}F</span>}
        {city.pending > 0 && <span>{city.pending}?</span>}
        <span className="text-muted-foreground/50">{total}</span>
      </div>
    </div>
  );
}

function TopicCard({ topic }: { topic: TopicCoalition }) {
  const [expanded, setExpanded] = useState(false);
  const displayCities = expanded ? topic.cities : topic.cities.slice(0, 6);
  const total = topic.total_passed + topic.total_failed + topic.total_pending;
  const pPct = total ? Math.round((topic.total_passed / total) * 100) : 0;
  const fPct = total ? Math.round((topic.total_failed / total) * 100) : 0;

  return (
    <Card className="overflow-hidden py-0 gap-0">
      <CardHeader className="p-4 border-b border-border">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-foreground">{topic.topic_label}</h3>
            <div className="flex items-center gap-3 mt-1.5">
              <MomentumBadge momentum={topic.momentum} />
              <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                {topic.city_count} cities
              </span>
              <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                {topic.bill_count} bills
              </span>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-lg font-bold font-[var(--font-mono)] text-green-600 dark:text-green-400">
              {pPct}%
            </div>
            <div className="text-xs text-muted-foreground">pass rate</div>
          </div>
        </div>

        {/* Outcome bar */}
        <div className="flex h-1.5 rounded-full overflow-hidden bg-muted mt-3">
          {pPct > 0 && <div className="bg-green-500" style={{ width: `${pPct}%` }} />}
          {fPct > 0 && <div className="bg-red-500" style={{ width: `${fPct}%` }} />}
          <div className="bg-amber-400 flex-1" />
        </div>

        <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
          <span>{topic.total_passed} passed</span>
          <span>{topic.total_failed} failed</span>
          <span>{topic.total_pending} pending</span>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* AI insight */}
        {topic.insight && (
          <div className="px-4 py-3 border-b border-border bg-muted/30">
            <p className="text-xs text-muted-foreground leading-relaxed">{topic.insight}</p>
          </div>
        )}

        {/* City list */}
        <div className="px-4 py-2 divide-y divide-border">
          {displayCities.map((city) => (
            <CityRow key={city.city} city={city} />
          ))}
        </div>

        {topic.cities.length > 6 && !expanded && (
          <Button
            variant="ghost"
            onClick={() => setExpanded(true)}
            className="w-full px-4 py-2 text-xs text-primary hover:bg-primary/5 transition-colors rounded-none border-t border-border"
          >
            Show {topic.cities.length - 6} more cities
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function CoalitionView() {
  const [data, setData] = useState<CoalitionsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchCoalitions();
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-6">
        <h2 className="text-page-heading uppercase tracking-tight text-foreground">Allies</h2>
        <p className="text-sm text-muted-foreground mt-1">
          See which cities are aligned on the issues you care about
        </p>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <svg className="animate-spin motion-reduce:animate-none h-6 w-6 text-primary" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm text-muted-foreground">Mapping alliances...</span>
        </div>
      )}

      {!loading && data && data.topics.length > 0 && (
        <>
          <div className="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
            <span className="font-[var(--font-mono)]">{data.total_topics} issues tracked</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500" /> Advancing
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" /> Stalled
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-400" /> Stable
            </span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.topics.map((topic, i) => (
              <div key={topic.topic} className="animate-fade-up" style={{ animationDelay: `${i * 80}ms` }}>
                <TopicCard topic={topic} />
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && (!data || data.topics.length === 0) && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">No coalition data available yet.</p>
            <p className="text-sm text-muted-foreground mt-1">Check back after the next data refresh.</p>
          </CardContent>
        </Card>
      )}
    </main>
  );
}

export default CoalitionView;
