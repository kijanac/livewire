<script lang="ts">
  import type { Bill } from "@/types";
  import { createBillSearch } from "@/hooks/use-bill-search.svelte";
  import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
  } from "@/components/ui/dialog";
  import { Input } from "@/components/ui/input";
  import { Button } from "@/components/ui/button";
  import { Badge } from "@/components/ui/badge";
  import Spinner from "./Spinner.svelte";
  import { formatTopic } from "@/lib/bill-utils";
  import Search from "@lucide/svelte/icons/search";

  let { existingBillIds, onAdd, onClose }: {
    existingBillIds: Set<number>;
    onAdd: (bill: Bill) => void;
    onClose: () => void;
  } = $props();

  const billSearch = createBillSearch();
</script>

<Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
  <DialogContent class="sm:max-w-2xl max-h-[80vh] flex flex-col">
    <DialogHeader>
      <DialogTitle>Add Bills</DialogTitle>
    </DialogHeader>

    <div class="py-3 border-b border-border">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" aria-hidden="true" />
        <Input
          type="text"
          value={billSearch.search}
          oninput={(e) => { const t = e.currentTarget as HTMLInputElement; billSearch.search = t.value; }}
          placeholder="Search by keyword, city, or bill number..."
          autofocus
          class="pl-9"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto py-3">
      {#if billSearch.loading}
        <div class="flex items-center justify-center py-8">
          <Spinner size={20} class="text-primary" />
        </div>
      {:else if billSearch.search.trim() && billSearch.results.length === 0}
        <p class="text-sm text-muted-foreground text-center py-8">
          No results for "{billSearch.search}"
        </p>
      {:else if !billSearch.search.trim()}
        <p class="text-sm text-muted-foreground text-center py-8">
          Start typing to find bills
        </p>
      {:else}
        <ul class="divide-y divide-border">
          {#each billSearch.results as bill (bill.id)}
            {@const alreadyAdded = existingBillIds.has(bill.id)}
            <li class="flex items-start justify-between gap-3 py-3">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-foreground line-clamp-2">
                  {bill.title}
                </p>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-xs text-muted-foreground">{bill.city_name}</span>
                  {#if bill.file_number}
                    <span class="text-xs text-muted-foreground font-[var(--font-mono)]">{bill.file_number}</span>
                  {/if}
                  {#if bill.status}
                    <span class="text-xs text-muted-foreground/70">{bill.status}</span>
                  {/if}
                </div>
                {#if bill.topics.length > 0}
                  <div class="flex flex-wrap gap-1 mt-1">
                    {#each bill.topics.slice(0, 3) as topic}
                      <Badge variant="secondary">{formatTopic(topic)}</Badge>
                    {/each}
                  </div>
                {/if}
              </div>
              <Button
                onclick={() => onAdd(bill)}
                disabled={alreadyAdded}
                size="sm"
                variant={alreadyAdded ? "secondary" : "default"}
                class="flex-shrink-0"
              >
                {alreadyAdded ? "Added" : "Add"}
              </Button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </DialogContent>
</Dialog>
