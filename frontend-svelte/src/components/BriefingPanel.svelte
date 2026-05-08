<script lang="ts">
  import { Card, CardContent } from "@/components/ui/card";
  import { Button } from "@/components/ui/button";
  import Spinner from "./Spinner.svelte";
  import X from "@lucide/svelte/icons/x";

  let { billId, onClose, onNavigate }: {
    billId: number;
    onClose: () => void;
    onNavigate?: (billId: number) => void;
  } = $props();
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm" tabindex="-1" />
<div class="fixed inset-y-0 right-0 z-50 w-full sm:max-w-xl bg-card shadow-xl overflow-y-auto">
  <div class="sticky top-0 bg-card border-b border-border px-4 py-3 flex items-center justify-between">
    <h3 class="text-sm font-bold text-foreground">Bill Briefing</h3>
    <Button variant="ghost" size="icon-sm" onclick={onClose} aria-label="Close briefing">
      <X class="h-4 w-4" />
    </Button>
  </div>
  <div class="p-4">
    <div class="flex items-center justify-center py-8">
      <Spinner size={20} class="text-primary" />
    </div>
    <p class="text-sm text-muted-foreground text-center">Briefing for bill #{billId} — full content coming in Phase 6</p>
  </div>
</div>
