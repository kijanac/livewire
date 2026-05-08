<script lang="ts">
  import { createCoalitions } from "@/hooks/use-coalitions.svelte";
  import { useErrorToast } from "@/hooks/use-error-toast.svelte";
  import type { TopicCoalition, CityAlignment } from "@/types";
  import { Card, CardHeader, CardContent } from "@/components/ui/card";
  import { Button } from "@/components/ui/button";
  import Spinner from "./components/Spinner.svelte";
  import { cn } from "@/lib/utils";
  import { CITY_STAGGER_MS, MOMENTUM_CONFIG } from "@/lib/visual-tokens";
  import { SvelteSet } from "svelte/reactivity";

  const coalitionsStore = createCoalitions();
  useErrorToast(coalitionsStore.error, "Failed to load coalitions");

  let expandedTopics = new SvelteSet<string>();
</script>

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
  <div class="mb-6">
    <h2 class="text-page-heading uppercase tracking-tight text-foreground">Allies</h2>
    <p class="text-sm text-muted-foreground mt-1">See which cities are aligned on the issues you care about</p>
  </div>

  {#if coalitionsStore.loading}
    <div class="flex flex-col items-center justify-center py-16 gap-3">
      <Spinner size={24} class="text-primary" />
      <span class="text-sm text-muted-foreground">Mapping alliances...</span>
    </div>
  {:else if coalitionsStore.data && coalitionsStore.data.topics.length > 0}
    <div class="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
      <span class="font-[var(--font-mono)]">{coalitionsStore.data.total_topics} issues tracked</span>
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500" /> Advancing</span>
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500" /> Stalled</span>
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400" /> Stable</span>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {#each coalitionsStore.data.topics as topic, i (topic.topic)}
        {@const total = topic.total_passed + topic.total_failed + topic.total_pending}
        {@const pPct = total ? Math.round((topic.total_passed / total) * 100) : 0}
        {@const fPct = total ? Math.round((topic.total_failed / total) * 100) : 0}
        {@const mom = MOMENTUM_CONFIG[topic.momentum as keyof typeof MOMENTUM_CONFIG] ?? MOMENTUM_CONFIG.stable}
        {@const expanded = expandedTopics.has(topic.topic)}
        {@const displayCities = expanded ? topic.cities : topic.cities.slice(0, 6)}

        <div class="animate-fade-up" style="animation-delay: {i * CITY_STAGGER_MS}ms">
          <Card class="overflow-hidden py-0 gap-0">
            <CardHeader class="p-4 border-b border-border">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h3 class="text-sm font-bold text-foreground">{topic.topic_label}</h3>
                  <div class="flex items-center gap-3 mt-1.5">
                    <span class={cn("inline-flex items-center gap-1 text-xs font-medium", mom.textColor)}>
                      <span class={cn("w-2 h-2 rounded-full", mom.color)} />
                      {mom.label}
                    </span>
                    <span class="text-xs font-[var(--font-mono)] text-muted-foreground">{topic.city_count} cities</span>
                    <span class="text-xs font-[var(--font-mono)] text-muted-foreground">{topic.bill_count} bills</span>
                  </div>
                </div>
                <div class="text-right flex-shrink-0">
                  <div class="text-lg font-bold font-[var(--font-mono)] text-green-600 dark:text-green-400">{pPct}%</div>
                  <div class="text-xs text-muted-foreground">pass rate</div>
                </div>
              </div>

              <div class="flex h-1.5 rounded-full overflow-hidden bg-muted mt-3">
                {#if pPct > 0}<div class="bg-green-500" style="width: {pPct}%" />{/if}
                {#if fPct > 0}<div class="bg-red-500" style="width: {fPct}%" />{/if}
                <div class="bg-amber-400 flex-1" />
              </div>

              <div class="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                <span>{topic.total_passed} passed</span>
                <span>{topic.total_failed} failed</span>
                <span>{topic.total_pending} pending</span>
              </div>
            </CardHeader>

            <CardContent class="p-0">
              {#if topic.insight}
                <div class="px-4 py-3 border-b border-border bg-muted/30">
                  <p class="text-xs text-muted-foreground leading-relaxed">{topic.insight}</p>
                </div>
              {/if}

              <div class="px-4 py-2 divide-y divide-border">
                {#each displayCities as city (city.city)}
                  {@const cTotal = city.passed + city.failed + city.pending}
                  {@const cMom = MOMENTUM_CONFIG[city.momentum as keyof typeof MOMENTUM_CONFIG] ?? MOMENTUM_CONFIG.stable}
                  <div class="flex items-center justify-between py-1.5">
                    <div class="flex items-center gap-2 min-w-0">
                      <span class="text-sm text-foreground truncate">{city.city_name}</span>
                      <span class={cn("inline-flex items-center gap-1 text-xs font-medium", cMom.textColor)}>
                        <span class={cn("w-2 h-2 rounded-full", cMom.color)} />
                        {cMom.label}
                      </span>
                    </div>
                    <div class="flex items-center gap-2 text-xs font-[var(--font-mono)] text-muted-foreground flex-shrink-0">
                      {#if city.passed > 0}<span class="text-green-600 dark:text-green-400">{city.passed}P</span>{/if}
                      {#if city.failed > 0}<span class="text-red-600 dark:text-red-400">{city.failed}F</span>{/if}
                      {#if city.pending > 0}<span>{city.pending}?</span>{/if}
                      <span class="text-muted-foreground/50">{cTotal}</span>
                    </div>
                  </div>
                {/each}
              </div>

              {#if topic.cities.length > 6 && !expanded}
                <Button variant="ghost" onclick={() => expandedTopics.add(topic.topic)}
                  class="w-full px-4 py-2 text-xs text-primary hover:bg-primary/5 transition-colors rounded-none border-t border-border">
                  Show {topic.cities.length - 6} more cities
                </Button>
              {/if}
            </CardContent>
          </Card>
        </div>
      {/each}
    </div>
  {:else}
    <Card>
      <CardContent class="p-12 text-center">
        <p class="text-muted-foreground">No coalition data available yet.</p>
        <p class="text-sm text-muted-foreground mt-1">Check back after the next data refresh.</p>
      </CardContent>
    </Card>
  {/if}
</main>
