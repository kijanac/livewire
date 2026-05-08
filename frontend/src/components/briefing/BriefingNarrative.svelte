<script lang="ts">
  import { Badge } from "@/components/ui/badge";
  import { Separator } from "@/components/ui/separator";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import type { NarrativeSection } from "@/types";

  let { narrative }: { narrative: NarrativeSection | null } = $props();
</script>

{#if narrative && (narrative.frames.length > 0 || narrative.talking_points.length > 0)}
  <div class="animate-fade-up p-4 sm:p-6" style="animation-delay: 400ms">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Narrative Analysis</h4>

    {#if narrative.frames.length > 0}
      <div class="mb-4">
        <span class="text-xs font-medium text-muted-foreground">Media Framing</span>
        <div class="mt-1.5 space-y-1.5">
          {#each narrative.frames as f}
            <div class="flex items-start gap-2">
              <span class="mt-1.5 w-2 h-2 rounded-full flex-shrink-0 {f.stance === 'support' ? 'bg-green-500' : f.stance === 'opposition' ? 'bg-red-500' : 'bg-muted-foreground/40'}" />
              <div class="min-w-0">
                <p class="text-sm text-foreground line-clamp-2">{f.headline}</p>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-xs text-muted-foreground">{f.source}</span>
                  <Badge variant="secondary" class="text-[10px] px-1 py-0">{f.frame}</Badge>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <div class="space-y-3">
      {#if narrative.support_narrative}
        <div class="p-3 rounded-md bg-green-500/5 border border-green-500/10">
          <span class="text-xs font-medium text-green-600 dark:text-green-400">Support Frame</span>
          <p class="text-sm text-foreground leading-relaxed mt-1">{narrative.support_narrative}</p>
        </div>
      {/if}
      {#if narrative.opposition_narrative}
        <div class="p-3 rounded-md bg-red-500/5 border border-red-500/10">
          <span class="text-xs font-medium text-red-600 dark:text-red-400">Opposition Frame</span>
          <p class="text-sm text-foreground leading-relaxed mt-1">{narrative.opposition_narrative}</p>
        </div>
      {/if}
    </div>

    {#if narrative.narrative_trajectory}
      <div class="mt-3 flex items-start gap-2">
        <TrendingUp class="w-3.5 h-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
        <p class="text-xs text-muted-foreground leading-relaxed">{narrative.narrative_trajectory}</p>
      </div>
    {/if}

    {#if narrative.talking_points.length > 0}
      <div class="mt-4 p-3 rounded-md bg-primary/5 border border-primary/10">
        <span class="text-xs font-bold text-primary uppercase tracking-wider">Talking Points</span>
        <ul class="mt-2 space-y-1.5">
          {#each narrative.talking_points as tp}
            <li class="flex items-start gap-2 text-sm text-foreground leading-relaxed">
              <span class="text-primary font-bold mt-px">&bull;</span> {tp}
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>
  <Separator />
{/if}
