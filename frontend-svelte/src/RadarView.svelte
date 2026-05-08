<script lang="ts">
  import { createRadar } from "@/hooks/use-radar.svelte";
  import { createTopics } from "@/hooks/use-topics.svelte";
  import type { RadarCluster, ClusterOutcomes } from "@/types";
  import { Card, CardHeader, CardContent } from "@/components/ui/card";
  import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
  } from "@/components/ui/select";
  import { Badge } from "@/components/ui/badge";
  import { Button } from "@/components/ui/button";
  import Spinner from "./components/Spinner.svelte";
  import { cn } from "@/lib/utils";
  import { getStatusClasses, formatTopic } from "@/lib/bill-utils";
  import { CLUSTER_STAGGER_MS, OUTCOME_INDICATORS } from "@/lib/visual-tokens";
  import Zap from "@lucide/svelte/icons/zap";

  const radarStore = createRadar();
  const { topics } = createTopics();
  let selectedBillId = $state<number | null>(null);
  let expandedClusters = $state(new Set<string>());
  function toggleCluster(label: string) {
    expandedClusters = new Set(expandedClusters);
    if (expandedClusters.has(label)) expandedClusters.delete(label);
    else expandedClusters.add(label);
  }

  const CLEAR = "__clear__";
</script>

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
  <!-- Header -->
  <div class="mb-6">
    <h2 class="text-page-heading uppercase tracking-tight text-foreground">Radar</h2>
    <p class="text-sm text-muted-foreground mt-1">Spot the same fights happening in different cities</p>
  </div>

  <!-- Topic filter -->
  <div class="flex items-center gap-3 mb-6">
    <span class="text-sm font-medium text-foreground">Filter by issue:</span>
    <Select
      value={radarStore.selectedTopic || undefined}
      onValueChange={(val) => {
        radarStore.selectedTopic = (!val || val === CLEAR) ? "" : (val ?? "");
      }}
    >
      <SelectTrigger>{radarStore.selectedTopic ? formatTopic(radarStore.selectedTopic) : "Any Issue"}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR}>Any Issue</SelectItem>
        {#each topics as topic (topic)}
          <SelectItem value={topic}>{formatTopic(topic)}</SelectItem>
        {/each}
      </SelectContent>
    </Select>
    {#if radarStore.radar && !radarStore.loading}
      <span class="text-sm font-[var(--font-mono)] text-muted-foreground">
        {radarStore.radar.total_clusters} cross-city pattern{radarStore.radar.total_clusters !== 1 ? "s" : ""} found
      </span>
    {/if}
  </div>

  <!-- Loading -->
  {#if radarStore.loading}
    <div class="flex flex-col items-center justify-center py-16 gap-3">
      <Spinner size={24} class="text-primary" />
      <span class="text-sm text-muted-foreground">Scanning for patterns...</span>
    </div>
  {:else if radarStore.radar && radarStore.radar.clusters.length === 0}
    <Card>
      <CardContent class="p-12 text-center">
        <p class="text-muted-foreground">
          No cross-city patterns yet{radarStore.selectedTopic ? ` for "${formatTopic(radarStore.selectedTopic)}"` : ""}.
        </p>
        <p class="text-sm text-muted-foreground mt-1">
          Try a different issue filter, or check back after the next data refresh.
        </p>
      </CardContent>
    </Card>
  {:else if radarStore.radar}
    <!-- Clusters grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {#each radarStore.radar.clusters as cluster, i (cluster.label)}
        {@const outcomes = cluster.outcomes}
        {@const total = outcomes ? outcomes.passed + outcomes.failed + outcomes.pending : 0}
        {@const pPct = total ? Math.round((outcomes!.passed / total) * 100) : 0}
        {@const fPct = total ? Math.round((outcomes!.failed / total) * 100) : 0}
        <div class="animate-fade-up" style="animation-delay: {i * CLUSTER_STAGGER_MS}ms">
          <Card class="overflow-hidden py-0 gap-0 border-l-4 border-l-primary">
            <!-- Cluster header -->
            <CardHeader class="p-4 border-b border-border">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h3 class="text-sm font-bold text-foreground">{cluster.label}</h3>
                  <div class="flex flex-wrap items-center gap-2 mt-1.5">
                    {#each cluster.cities as city}
                      <Badge variant="secondary">{city}</Badge>
                    {/each}
                  </div>
                </div>
                <div class="text-right flex-shrink-0">
                  <div class="text-lg font-bold font-[var(--font-mono)] text-foreground">{cluster.city_count}</div>
                  <div class="text-xs text-muted-foreground">{cluster.city_count === 1 ? "city" : "cities"}</div>
                </div>
              </div>
              <div class="text-xs font-[var(--font-mono)] text-muted-foreground mt-2">
                {cluster.bill_count} bill{cluster.bill_count !== 1 ? "s" : ""}
              </div>
            </CardHeader>

            <!-- Outcome indicators -->
            {#if outcomes}
              <div class="px-4 py-3 border-b border-border bg-muted/30 space-y-2">
                <div class="flex items-center gap-3 text-xs">
                  {#each OUTCOME_INDICATORS as { key, color, label }}
                    {#if outcomes[key]}
                      <span class="flex items-center gap-1">
                        <span class={cn("inline-block w-2 h-2 rounded-full", color)} />
                        <span class="font-medium text-foreground">{outcomes[key]}</span>
                        <span class="text-muted-foreground">{label}</span>
                      </span>
                    {/if}
                  {/each}
                  {#if outcomes.avg_days_to_resolution != null}
                    <span class="text-muted-foreground ml-auto font-[var(--font-mono)]">
                      ~{outcomes.avg_days_to_resolution < 60
                        ? `${Math.round(outcomes.avg_days_to_resolution)}d`
                        : `${Math.round(outcomes.avg_days_to_resolution / 30)}mo`} avg
                    </span>
                  {/if}
                </div>

                {#if total > 1}
                  <div class="flex h-1.5 rounded-full overflow-hidden bg-muted">
                    {#if pPct > 0}<div class="bg-green-500" style="width: {pPct}%" />{/if}
                    {#if fPct > 0}<div class="bg-red-500" style="width: {fPct}%" />{/if}
                    <div class="bg-amber-400 flex-1" />
                  </div>
                {/if}

                {#if outcomes.velocity_flag}
                  <div class="flex items-center gap-1.5 text-xs font-medium text-primary">
                    <Zap class="w-3.5 h-3.5 flex-shrink-0" />
                    <span>{total} bills in {outcomes.intro_span_days} days — possible coordinated campaign</span>
                  </div>
                {/if}

                {#if outcomes.insight}
                  <p class="text-xs text-muted-foreground leading-relaxed">{outcomes.insight}</p>
                {/if}
              </div>
            {/if}

            <!-- Bills in cluster -->
            <CardContent class="p-0">
              {#each cluster.bills.slice(0, expandedClusters.has(cluster.label) ? undefined : 6) as bill (bill.id)}
                <Button
                  variant="ghost"
                  onclick={() => (selectedBillId = bill.id)}
                  class={cn(
                    "w-full text-left px-4 py-3 h-auto rounded-none justify-start items-start flex-col",
                    bill.urgency === "urgent"
                      ? "border-l-4 border-l-primary"
                      : bill.urgency === "soon"
                        ? "border-l-4 border-l-accent"
                        : ""
                  )}
                >
                  <div class="flex items-center gap-2 mb-0.5">
                    <span class="text-xs font-medium text-muted-foreground">{bill.city_name}, {bill.state}</span>
                    {#if bill.file_number}
                      <span class="text-xs text-muted-foreground font-[var(--font-mono)]">{bill.file_number}</span>
                    {/if}
                    {#if bill.urgency === "urgent"}
                      <Badge class="bg-primary text-primary-foreground">This Week</Badge>
                    {/if}
                  </div>
                  <p class="text-sm text-foreground line-clamp-2 whitespace-normal">{bill.title}</p>
                  <div class="flex items-center gap-2 mt-1">
                    {#if bill.status}
                      <Badge class={getStatusClasses(bill.status)}>{bill.status}</Badge>
                    {/if}
                  </div>
                </Button>
              {/each}

              {#if cluster.bills.length > 6 && !expandedClusters.has(cluster.label)}
                <Button variant="ghost" onclick={() => toggleCluster(cluster.label)}
                  class="w-full px-4 py-2 text-xs text-primary hover:bg-primary/5 transition-colors rounded-none border-t border-border">
                  Show {cluster.bills.length - 6} more
                </Button>
              {/if}
            </CardContent>
          </Card>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Briefing -->
  {#if selectedBillId !== null}
    {#await import("./components/BriefingPanel.svelte") then { default: BriefingPanel }}
      <BriefingPanel billId={selectedBillId} onClose={() => (selectedBillId = null)} onNavigate={(id: number) => (selectedBillId = id)} />
    {/await}
  {/if}
</main>
