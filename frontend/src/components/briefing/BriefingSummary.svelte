<script lang="ts">
  import { Separator } from "@/components/ui/separator";

  let { summary, impact }: { summary: string | null; impact: string | null } = $props();
</script>

{#if summary}
  <div class="animate-fade-up p-4 sm:p-6" style="animation-delay: 75ms">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Summary</h4>
    <p class="text-sm text-foreground leading-relaxed">{summary}</p>
  </div>
  <Separator />
{/if}
{#if impact}
  <div class="animate-fade-up p-4 sm:p-6 bg-primary/5 border-l-4 border-primary" style="animation-delay: 150ms">
    <h4 class="text-xs font-bold text-primary uppercase tracking-wider mb-2">Why This Matters</h4>
    <p class="text-sm text-foreground leading-relaxed">{impact}</p>
  </div>
  <Separator />
{/if}
