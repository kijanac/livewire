<script lang="ts">
  import { Separator } from "@/components/ui/separator";

  let { organizing }: { organizing: string | null } = $props();
</script>

{#if organizing}
  <div class="animate-fade-up p-4 sm:p-6 bg-accent/10 border-l-4 border-accent" style="animation-delay: 275ms">
    <h4 class="text-xs font-bold text-foreground uppercase tracking-wider mb-2">Organizing Activity</h4>
    <p class="text-sm text-foreground leading-relaxed">{organizing}</p>
  </div>
  <Separator />
{/if}
