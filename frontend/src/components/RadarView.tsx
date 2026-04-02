import { useState, lazy, Suspense } from "react";
import { useRadar } from "../hooks/useRadar";
import { useTopics } from "../hooks/useTopics";
import type { RadarCluster, ClusterOutcomes } from "../types";
const BriefingPanel = lazy(() => import("./BriefingPanel"));
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getStatusClasses, formatTopic } from "@/lib/bill-utils";
import { Zap } from "lucide-react";

const OUTCOME_INDICATORS = [
  { key: "passed", color: "bg-green-500", label: "passed" },
  { key: "failed", color: "bg-red-500", label: "failed" },
  { key: "pending", color: "bg-amber-400", label: "pending" },
] as const;

function OutcomeBar({ outcomes }: { outcomes: ClusterOutcomes }) {
  const total = outcomes.passed + outcomes.failed + outcomes.pending;
  const pPct = total ? Math.round((outcomes.passed / total) * 100) : 0;
  const fPct = total ? Math.round((outcomes.failed / total) * 100) : 0;

  return (
    <div className="px-4 py-3 border-b border-border bg-muted/30 space-y-2">
      <div className="flex items-center gap-3 text-xs">
        {OUTCOME_INDICATORS.map(({ key, color, label }) => {
          const count = outcomes[key];
          if (!count) return null;
          return (
            <span key={key} className="flex items-center gap-1">
              <span className={cn("inline-block w-2 h-2 rounded-full", color)} />
              <span className="font-medium text-foreground">{count}</span>
              <span className="text-muted-foreground">{label}</span>
            </span>
          );
        })}
        {outcomes.avg_days_to_resolution != null && (
          <span className="text-muted-foreground ml-auto font-[var(--font-mono)]">
            ~{outcomes.avg_days_to_resolution < 60
              ? `${Math.round(outcomes.avg_days_to_resolution)}d`
              : `${Math.round(outcomes.avg_days_to_resolution / 30)}mo`} avg
          </span>
        )}
      </div>

      {total > 1 && (
        <div className="flex h-1.5 rounded-full overflow-hidden bg-muted">
          {pPct > 0 && <div className="bg-green-500" style={{ width: `${pPct}%` }} />}
          {fPct > 0 && <div className="bg-red-500" style={{ width: `${fPct}%` }} />}
          <div className="bg-amber-400 flex-1" />
        </div>
      )}

      {outcomes.velocity_flag && (
        <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
          <Zap className="w-3.5 h-3.5 flex-shrink-0" />
          <span>
            {total} bills in {outcomes.intro_span_days} days — possible coordinated campaign
          </span>
        </div>
      )}

      {outcomes.insight && (
        <p className="text-xs text-muted-foreground leading-relaxed">
          {outcomes.insight}
        </p>
      )}
    </div>
  );
}

function ClusterCard({
  cluster,
  onBillClick,
}: {
  cluster: RadarCluster;
  onBillClick: (billId: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const displayBills = expanded ? cluster.bills : cluster.bills.slice(0, 6);

  return (
    <Card className="overflow-hidden py-0 gap-0 border-l-4 border-l-primary">
      {/* Cluster header */}
      <CardHeader className="p-4 border-b border-border">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-foreground">
              {cluster.label}
            </h3>
            <div className="flex flex-wrap items-center gap-2 mt-1.5">
              {cluster.cities.map((city) => (
                <Badge
                  key={city}
                  variant="secondary"
                >
                  {city}
                </Badge>
              ))}
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-lg font-bold font-[var(--font-mono)] text-foreground">
              {cluster.city_count}
            </div>
            <div className="text-xs text-muted-foreground">
              {cluster.city_count === 1 ? "city" : "cities"}
            </div>
          </div>
        </div>
        <div className="text-xs font-[var(--font-mono)] text-muted-foreground mt-2">
          {cluster.bill_count} bill{cluster.bill_count !== 1 ? "s" : ""}
        </div>
      </CardHeader>

      {/* Outcome indicators */}
      {cluster.outcomes && <OutcomeBar outcomes={cluster.outcomes} />}

      {/* Bills in cluster */}
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {displayBills.map((bill) => (
            <Button
              key={bill.id}
              variant="ghost"
              onClick={() => onBillClick(bill.id)}
              className={cn(
                "w-full text-left px-4 py-3 h-auto rounded-none justify-start items-start flex-col",
                bill.urgency === "urgent"
                  ? "border-l-4 border-l-primary"
                  : bill.urgency === "soon"
                    ? "border-l-4 border-l-accent"
                    : ""
              )}
            >
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-xs font-medium text-muted-foreground">
                  {bill.city_name}, {bill.state}
                </span>
                {bill.file_number && (
                  <span className="text-xs text-muted-foreground font-[var(--font-mono)]">
                    {bill.file_number}
                  </span>
                )}
                {bill.urgency === "urgent" && (
                  <Badge className="bg-primary text-primary-foreground">
                    This Week
                  </Badge>
                )}
              </div>
              <p className="text-sm text-foreground line-clamp-2 whitespace-normal">
                {bill.title}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {bill.status && (
                  <Badge className={getStatusClasses(bill.status)}>
                    {bill.status}
                  </Badge>
                )}
              </div>
            </Button>
          ))}
        </div>

        {cluster.bills.length > 6 && !expanded && (
          <Button
            variant="ghost"
            onClick={() => setExpanded(true)}
            className="w-full px-4 py-2 text-xs text-primary hover:bg-primary/5 transition-colors rounded-none border-t border-border"
          >
            Show {cluster.bills.length - 6} more
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function RadarView() {
  const { radar, selectedTopic, setSelectedTopic, loading } = useRadar();
  const topics = useTopics();
  const [selectedBillId, setSelectedBillId] = useState<number | null>(null);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-page-heading uppercase tracking-tight text-foreground">Radar</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Spot the same fights happening in different cities
        </p>
      </div>

      {/* Topic filter */}
      <div className="flex items-center gap-3 mb-6">
        <span className="text-sm font-medium text-foreground">
          Filter by issue:
        </span>
        <Select
          key={selectedTopic ? "topic-set" : "topic-empty"}
          value={selectedTopic || undefined}
          onValueChange={(val) => setSelectedTopic(!val || val === "__clear__" ? "" : val)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Any Issue" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__clear__">Any Issue</SelectItem>
            {topics.map((topic) => (
              <SelectItem key={topic} value={topic}>
                {formatTopic(topic)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {radar && !loading && (
          <span className="text-sm font-[var(--font-mono)] text-muted-foreground">
            {radar.total_clusters} cross-city pattern{radar.total_clusters !== 1 ? "s" : ""} found
          </span>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <svg
            className="animate-spin motion-reduce:animate-none h-6 w-6 text-primary"
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
          <span className="text-sm text-muted-foreground">
            Scanning for patterns...
          </span>
        </div>
      )}

      {/* Empty state */}
      {!loading && radar && radar.clusters.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">
              No cross-city patterns yet
              {selectedTopic ? ` for "${formatTopic(selectedTopic)}"` : ""}.
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Try a different issue filter, or check back after the next data refresh.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Clusters grid */}
      {!loading && radar && radar.clusters.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {radar.clusters.map((cluster, i) => (
            <div key={cluster.label} className="animate-fade-up" style={{ animationDelay: `${i * 100}ms` }}>
              <ClusterCard
                cluster={cluster}
                onBillClick={setSelectedBillId}
              />
            </div>
          ))}
        </div>
      )}

      {/* Briefing panel */}
      {selectedBillId !== null && (
        <Suspense fallback={null}>
          <BriefingPanel
            billId={selectedBillId}
            onClose={() => setSelectedBillId(null)}
            onNavigate={setSelectedBillId}
          />
        </Suspense>
      )}
    </main>
  );
}

export default RadarView;
