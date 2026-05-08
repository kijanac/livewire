<script lang="ts">
  import { Separator } from "@/components/ui/separator";

  let { reception }: { reception: string | null } = $props();
</script>

{#if reception}
  <div class="animate-fade-up p-4 sm:p-6" style="animation-delay: 350ms">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Public Reception</h4>
    <p class="text-sm text-foreground leading-relaxed">{reception}</p>
  </div>
  <Separator />
{/if}
