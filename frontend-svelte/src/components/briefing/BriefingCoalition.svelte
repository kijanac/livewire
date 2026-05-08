<script lang="ts">
  import { Badge } from "@/components/ui/badge";
  import { Separator } from "@/components/ui/separator";
  import type { CoalitionBrief } from "@/types";

  let { coalition }: { coalition: CoalitionBrief | null } = $props();
</script>

{#if coalition && (coalition.ally_cities.length > 0 || coalition.contested_cities.length > 0 || coalition.insight)}
  <div class="animate-fade-up p-4 sm:p-6 bg-accent/5 border-l-4 border-accent" style="animation-delay: 450ms">
    <h4 class="text-xs font-bold text-foreground uppercase tracking-wider mb-3">Coalition Intel</h4>

    {#if coalition.ally_cities.length > 0}
      <div class="mb-3">
        <span class="text-xs font-medium text-green-600 dark:text-green-400">Allies (passed similar bills)</span>
        <div class="flex flex-wrap gap-1.5 mt-1.5">
          {#each coalition.ally_cities as city}
            <Badge variant="secondary" class="bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20">{city}</Badge>
          {/each}
        </div>
      </div>
    {/if}

    {#if coalition.contested_cities.length > 0}
      <div class="mb-3">
        <span class="text-xs font-medium text-amber-600 dark:text-amber-400">In play (still deciding)</span>
        <div class="flex flex-wrap gap-1.5 mt-1.5">
          {#each coalition.contested_cities as city}
            <Badge variant="secondary" class="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20">{city}</Badge>
          {/each}
        </div>
      </div>
    {/if}

    {#if coalition.insight}
      <div class="mt-3 p-3 rounded-md bg-accent/10 border border-accent/20">
        <p class="text-sm text-foreground leading-relaxed">{coalition.insight}</p>
      </div>
    {/if}
  </div>
  <Separator />
{/if}
