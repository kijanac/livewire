<script lang="ts">
  import { createBriefing } from "@/hooks/use-briefing.svelte";
  import { useErrorToast } from "@/hooks/use-error-toast.svelte";
  import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
  } from "@/components/ui/sheet";
  import { Badge } from "@/components/ui/badge";
  import { Button } from "@/components/ui/button";
  import { Separator } from "@/components/ui/separator";
  import Spinner from "./Spinner.svelte";
  import { formatTopic, getStatusClasses } from "@/lib/bill-utils";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import BriefingSummary from "./briefing/BriefingSummary.svelte";
  import BriefingPower from "./briefing/BriefingPower.svelte";
  import BriefingOrganizing from "./briefing/BriefingOrganizing.svelte";
  import BriefingReception from "./briefing/BriefingReception.svelte";
  import BriefingNarrative from "./briefing/BriefingNarrative.svelte";
  import BriefingTimeline from "./briefing/BriefingTimeline.svelte";
  import BriefingDocuments from "./briefing/BriefingDocuments.svelte";
  import BriefingNews from "./briefing/BriefingNews.svelte";
  import BriefingSimilar from "./briefing/BriefingSimilar.svelte";
  import BriefingCoalition from "./briefing/BriefingCoalition.svelte";
  import BriefingNotes from "./briefing/BriefingNotes.svelte";

  let { billId, onClose, onNavigate }: {
    billId: number;
    onClose: () => void;
    onNavigate?: (billId: number) => void;
  } = $props();

  const briefingStore = createBriefing(billId);
  useErrorToast(briefingStore.error, "Failed to load briefing");

  function handleNavigate(id: number) {
    briefingStore.navigateTo(id);
    onNavigate?.(id);
  }
</script>

<Sheet open onOpenChange={(open) => { if (!open) onClose(); }}>
  <SheetContent side="right" class="w-full sm:max-w-lg overflow-hidden flex flex-col">
    <SheetHeader class="flex-shrink-0">
      <div class="flex items-center gap-2">
        {#if briefingStore.history.length > 0}
          <Button variant="ghost" size="icon-sm" onclick={briefingStore.goBack} title="Previous bill">
            <ArrowLeft class="h-5 w-5" />
          </Button>
        {/if}
        <SheetTitle>Intel Briefing</SheetTitle>
      </div>
    </SheetHeader>

    <div class="flex-1 overflow-y-auto overscroll-contain">
      {#if briefingStore.loading}
        <div class="flex flex-col items-center justify-center py-16 gap-3">
          <Spinner size={24} class="text-primary" />
          <span class="text-sm text-muted-foreground">Building briefing...</span>
        </div>
      {/if}

      {#if briefingStore.error}
        <div class="p-4 sm:p-6">
          <p class="text-sm text-destructive">{briefingStore.error}</p>
        </div>
      {/if}

      {#if !briefingStore.loading && briefingStore.briefing}
        {@const briefing = briefingStore.briefing}
        <div>
          <div class="animate-fade-up p-4 sm:p-6">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs font-medium text-muted-foreground">{briefing.bill.city_name}, {briefing.bill.state}</span>
              {#if briefing.bill.file_number}<span class="text-xs text-muted-foreground font-[var(--font-mono)]">{briefing.bill.file_number}</span>{/if}
              {#if briefing.bill.urgency === "urgent"}<Badge class="bg-primary text-primary-foreground">This Week</Badge>{/if}
              {#if briefing.bill.urgency === "soon"}<Badge variant="secondary">This Month</Badge>{/if}
            </div>
            <h3 class="text-section-heading text-foreground mb-2">{briefing.bill.title}</h3>
            <div class="flex flex-wrap items-center gap-2">
              {#if briefing.bill.status}<Badge class={getStatusClasses(briefing.bill.status)}>{briefing.bill.status}</Badge>{/if}
              {#each briefing.bill.topics as t}<Badge variant="secondary">{formatTopic(t)}</Badge>{/each}
            </div>
            {#if briefing.bill.url}
              <a href={briefing.bill.url} target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80 mt-2">
                Read full legislation <ExternalLink class="h-3 w-3" />
              </a>
            {/if}
          </div>

          <Separator />

          <BriefingSummary summary={briefing.summary} impact={briefing.impact} />
          <BriefingPower power={briefing.power} />
          <BriefingOrganizing organizing={briefing.organizing} />
          <BriefingReception reception={briefing.reception} />
          <BriefingNarrative narrative={briefing.narrative} />
          <BriefingTimeline timeline={briefing.timeline} />
          <BriefingDocuments documents={briefing.documents} />
          <BriefingNews news={briefing.news} />
          <BriefingSimilar similarBills={briefing.similar_bills} onNavigate={handleNavigate} />
          <BriefingCoalition coalition={briefing.coalition} />
          <BriefingNotes notes={briefing.collection_notes} />
        </div>
      {/if}
    </div>
  </SheetContent>
</Sheet>
