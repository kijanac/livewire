<script lang="ts">
  import { Separator } from "@/components/ui/separator";
  import { formatDate } from "@/lib/bill-utils";

  let { timeline }: { timeline: { event: string; date: string }[] } = $props();
</script>

{#if timeline.length > 0}
  <div class="p-4 sm:p-6">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Timeline</h4>
    <div class="space-y-2">
      {#each timeline as event}
        <div class="flex items-center gap-3">
          <div class="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
          <span class="text-sm text-foreground font-medium">{event.event}</span>
          <span class="text-xs font-[var(--font-mono)] text-muted-foreground">{formatDate(event.date)}</span>
        </div>
      {/each}
    </div>
  </div>
  <Separator />
{/if}
