<script lang="ts">
  import type { StatsResponse } from "@/types";
  import { Card, CardContent } from "@/components/ui/card";
  import { Badge } from "@/components/ui/badge";
  import { cn } from "@/lib/utils";
  import { formatTopic } from "@/lib/bill-utils";
  import { staggerDelay } from "@/lib/visual-tokens";

  let { stats, loading }: { stats: StatsResponse | null; loading: boolean } = $props();
</script>

{#if loading || !stats}
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-6">
    {#each Array(4) as _, i}
      <Card class="animate-pulse motion-reduce:animate-none">
        <CardContent>
          <div class="h-4 bg-muted rounded w-20 mb-3" />
          <div class="h-8 bg-muted rounded w-16 mb-2" />
          <div class="h-3 bg-muted rounded w-24" />
        </CardContent>
      </Card>
    {/each}
  </div>
{:else}

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-6">
    <!-- Up for Action This Week -->
    <Card class={cn("animate-fade-up", stats.moving_this_week > 0 && "bg-primary text-primary-foreground border-primary")}>
      <CardContent>
        <div class={cn("text-xs font-medium uppercase tracking-wider mb-1", stats.moving_this_week > 0 ? "text-primary-foreground/80" : "text-muted-foreground")}>
          Up for Action This Week
        </div>
        <div class={cn("text-hero-number", stats.moving_this_week > 0 ? "text-primary-foreground" : "text-foreground")}>
          {stats.moving_this_week}
        </div>
        <div class={cn("text-xs mt-1", stats.moving_this_week > 0 ? "text-primary-foreground/70" : "text-muted-foreground")}>
          bills with hearings or votes in 7 days
        </div>
      </CardContent>
    </Card>

    <!-- Trending Issues -->
    <Card class="animate-fade-up" style={staggerDelay(1)}>
      <CardContent>
        <div class="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Trending Issues
        </div>
        {#if stats.hot_topics.length > 0}
          <div class="flex flex-col gap-1.5">
            {#each stats.hot_topics as t}
              <div class="flex items-center justify-between">
                <Badge variant="secondary">
                  {formatTopic(t.topic)}
                </Badge>
                <span class="text-xs font-[var(--font-mono)] text-muted-foreground">
                  {t.count}
                </span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-sm text-muted-foreground">Issue tags loading...</div>
        {/if}
      </CardContent>
    </Card>

    <!-- Hottest City -->
    <Card class="animate-fade-up" style={staggerDelay(2)}>
      <CardContent>
        <div class="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
          Hottest City
        </div>
        {#if stats.most_active_city}
          <div class="text-page-heading text-foreground">
            {stats.most_active_city.city_name}
          </div>
          <div class="text-xs text-muted-foreground mt-1">
            {stats.most_active_city.upcoming_count} hearing{stats.most_active_city.upcoming_count !== 1 ? "s" : ""} this week
          </div>
        {:else}
          <div class="text-sm text-muted-foreground mt-2">No hearings scheduled</div>
        {/if}
      </CardContent>
    </Card>

    <!-- Just Filed -->
    <Card class={cn("animate-fade-up", stats.new_bills_7d > 0 && "bg-accent text-accent-foreground border-accent")} style={staggerDelay(3)}>
      <CardContent>
        <div class={cn("text-xs font-medium uppercase tracking-wider mb-1", stats.new_bills_7d > 0 ? "text-accent-foreground/80" : "text-muted-foreground")}>
          Just Filed
        </div>
        <div class={cn("text-hero-number", stats.new_bills_7d > 0 ? "text-accent-foreground" : "text-foreground")}>
          {stats.new_bills_7d}
        </div>
        <div class={cn("text-xs mt-1", stats.new_bills_7d > 0 ? "text-accent-foreground/70" : "text-muted-foreground")}>
          new bills this week
        </div>
      </CardContent>
    </Card>
  </div>
{/if}
