<script lang="ts">
  import { Badge } from "@/components/ui/badge";
  import { Button } from "@/components/ui/button";
  import { Separator } from "@/components/ui/separator";
  import { getStatusClasses } from "@/lib/bill-utils";
  import type { SimilarBill } from "@/types";

  let { similarBills, onNavigate }: { similarBills: SimilarBill[]; onNavigate: (id: number) => void } = $props();
</script>

{#if similarBills.length > 0}
  <div class="p-4 sm:p-6">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Same Fight, Other Cities</h4>
    <div class="space-y-2">
      {#each similarBills as b (b.id)}
        <Button variant="outline" onclick={() => onNavigate(b.id)}
          class="w-full text-left h-auto p-3 justify-start items-start flex-col hover:border-primary transition-colors cursor-pointer whitespace-normal">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-medium text-muted-foreground">{b.city_name}, {b.state}</span>
            {#if b.file_number}<span class="text-xs text-muted-foreground font-[var(--font-mono)]">{b.file_number}</span>{/if}
            {#if b.status}<Badge class={getStatusClasses(b.status)}>{b.status}</Badge>{/if}
          </div>
          <p class="text-sm text-foreground line-clamp-2">{b.title}</p>
        </Button>
      {/each}
    </div>
  </div>
  <Separator />
{/if}
