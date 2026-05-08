<script lang="ts">
  import type { Bill } from "@/types";
  import { Card, CardContent } from "@/components/ui/card";
  import { Badge } from "@/components/ui/badge";
  import { cn } from "@/lib/utils";
  import { formatShortDate, daysUntil } from "@/lib/bill-utils";
  import { staggerDelay } from "@/lib/visual-tokens";

  let { bills, loading }: { bills: Bill[]; loading: boolean } = $props();
  let selectedBillId = $state<number | null>(null);
</script>

{#if loading}
  <div class="mb-6">
    <h2 class="flex items-center gap-2 text-section-heading uppercase tracking-wider text-foreground mb-3">
      <span class="inline-block w-3 h-3 bg-primary" aria-hidden="true" />
      Coming Up
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {#each [1, 2, 3] as i}
        <Card class="animate-pulse motion-reduce:animate-none">
          <CardContent>
            <div class="h-4 bg-muted rounded w-1/3 mb-2" />
            <div class="h-3 bg-muted rounded w-full mb-1" />
            <div class="h-3 bg-muted rounded w-2/3" />
          </CardContent>
        </Card>
      {/each}
    </div>
  </div>
{:else if bills.length === 0}
  <!-- nothing -->
{:else}
  <div class="mb-6">
    <h2 class="flex items-center gap-2 text-section-heading uppercase tracking-wider text-foreground mb-3">
      <span class="inline-block w-3 h-3 bg-primary" aria-hidden="true" />
      Coming Up
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {#each bills.slice(0, 6) as bill, i (bill.id)}
        {@const days = daysUntil(bill.agenda_date)}
        {@const isUrgent = bill.urgency === "urgent"}

        <button
          onclick={() => (selectedBillId = bill.id)}
          class="block text-left w-full"
        >
          <Card
            class={cn(
              "animate-fade-up transition-shadow hover:shadow-md h-full cursor-pointer",
              isUrgent ? "border-l-4 border-l-primary" : "border-l-4 border-l-accent"
            )}
            style={staggerDelay(i)}
          >
            <CardContent>
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-medium text-muted-foreground">
                  {bill.city_name}, {bill.state}
                </span>
                <Badge
                  class={cn(isUrgent && "bg-primary text-primary-foreground")}
                  variant={isUrgent ? "default" : "secondary"}
                >
                  {days !== null && days <= 0
                    ? "Today"
                    : days === 1
                      ? "Tomorrow"
                      : `${days} days`}
                </Badge>
              </div>
              <p class="text-sm font-medium text-foreground line-clamp-2 mb-1" title={bill.title}>
                {bill.title}
              </p>
              <div class="flex items-center gap-2 text-xs text-muted-foreground">
                {#if bill.file_number}
                  <span class="font-[var(--font-mono)]">{bill.file_number}</span>
                {/if}
                <span>{formatShortDate(bill.agenda_date)}</span>
              </div>
            </CardContent>
          </Card>
        </button>
      {/each}
    </div>

    {#if selectedBillId !== null}
      {#await import("./BriefingPanel.svelte") then { default: BriefingPanel }}
        <BriefingPanel billId={selectedBillId} onClose={() => (selectedBillId = null)} />
      {/await}
    {/if}
  </div>
{/if}
