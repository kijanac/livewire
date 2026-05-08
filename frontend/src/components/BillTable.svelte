<script lang="ts">
  import type { Bill } from "@/types";
  import {
    Table,
    TableHeader,
    TableBody,
    TableRow,
    TableHead,
    TableCell,
  } from "@/components/ui/table";
  import { Badge } from "@/components/ui/badge";
  import { Button } from "@/components/ui/button";
  import Spinner from "./Spinner.svelte";
  import { cn } from "@/lib/utils";
  import { formatDate, formatTopic, getStatusClasses } from "@/lib/bill-utils";
  import { ROW_STAGGER_MS } from "@/lib/visual-tokens";
  import ExternalLink from "@lucide/svelte/icons/external-link";

  let { bills, total, page, perPage, onPageChange, loading }: {
    bills: Bill[];
    total: number;
    page: number;
    perPage: number;
    onPageChange: (page: number) => void;
    loading: boolean;
  } = $props();

  let selectedBillId = $state<number | null>(null);
  let totalPages = $derived(Math.max(1, Math.ceil(total / perPage)));
</script>

{#if loading}
  <div class="bg-card rounded-lg shadow-sm p-12 text-center">
    <div class="inline-flex items-center gap-2 text-muted-foreground">
      <Spinner size={20} />
      Loading...
    </div>
  </div>
{:else if bills.length === 0}
  <div class="bg-card rounded-lg shadow-sm p-12 text-center">
    <p class="text-muted-foreground">No bills match your filters.</p>
    <p class="text-sm text-muted-foreground/70 mt-1">
      Try broadening your search or clearing a filter.
    </p>
  </div>
{:else}
  <div class="bg-card rounded-lg shadow-sm overflow-hidden">
    <Table>
      <TableHeader class="bg-muted/50">
        <TableRow>
          <TableHead class="px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
            Jurisdiction
          </TableHead>
          <TableHead class="px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
            Bill
          </TableHead>
          <TableHead class="px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
            Status
          </TableHead>
          <TableHead class="hidden md:table-cell px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
            Topics
          </TableHead>
          <TableHead class="hidden lg:table-cell px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
            Introduced
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {#each bills as bill, i (bill.id)}
          <TableRow
            onclick={() => (selectedBillId = bill.id)}
            class={cn(
              "animate-fade-up cursor-pointer",
              bill.urgency === "urgent" && "border-l-4 border-l-primary",
              bill.urgency === "soon" && "border-l-4 border-l-accent"
            )}
            style="animation-delay: {i * ROW_STAGGER_MS}ms"
          >
            <TableCell class="px-2 py-2 sm:px-4 sm:py-3 text-sm text-foreground align-top">
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-1.5">
                  <span class="font-medium">{bill.city_name}</span>
                  {#if bill.jurisdiction_level === "state"}
                    <Badge variant="outline" class="text-[10px] px-1 py-0 h-4">State</Badge>
                  {/if}
                </div>
                {#if bill.urgency === "urgent"}
                  <Badge class="bg-primary text-primary-foreground w-fit">This Week</Badge>
                {:else if bill.urgency === "soon"}
                  <Badge variant="secondary" class="w-fit">This Month</Badge>
                {/if}
              </div>
            </TableCell>
            <TableCell class="px-2 py-2 sm:px-4 sm:py-3 align-top whitespace-normal">
              <p class="text-sm text-foreground line-clamp-2" title={bill.title}>
                {bill.title}
              </p>
              {#if bill.summary}
                <p class="text-xs text-muted-foreground mt-0.5 line-clamp-1 italic">
                  {bill.summary}
                </p>
              {/if}
              <div class="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                {#if bill.file_number}
                  <span class="font-[var(--font-mono)]">{bill.file_number}</span>
                {/if}
                {#if bill.type_name}
                  <span>{bill.type_name}</span>
                {/if}
                {#if bill.url}
                  <a
                    href={bill.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onclick={(e) => e.stopPropagation()}
                    class="inline-flex items-center gap-0.5 text-muted-foreground hover:text-primary transition-colors"
                    title="View on city council site"
                  >
                    <ExternalLink class="h-3 w-3" />
                  </a>
                {/if}
              </div>
            </TableCell>
            <TableCell class="px-2 py-2 sm:px-4 sm:py-3 align-top">
              {#if bill.status}
                <Badge class={getStatusClasses(bill.status)}>
                  {bill.status}
                </Badge>
              {:else}
                <span class="text-sm text-muted-foreground">-</span>
              {/if}
            </TableCell>
            <TableCell class="hidden md:table-cell px-2 py-2 sm:px-4 sm:py-3 align-top">
              <div class="flex flex-wrap gap-1">
                {#each bill.topics.slice(0, 3) as topic}
                  <Badge variant="secondary">{formatTopic(topic)}</Badge>
                {/each}
              </div>
            </TableCell>
            <TableCell class="hidden lg:table-cell px-2 py-2 sm:px-4 sm:py-3 text-sm font-[var(--font-mono)] text-muted-foreground align-top">
              {formatDate(bill.intro_date)}
            </TableCell>
          </TableRow>
        {/each}
      </TableBody>
    </Table>

    <div class="flex flex-col sm:flex-row items-center justify-between border-t border-border px-4 py-3 bg-muted/50 gap-2 sm:gap-0">
      <div class="text-xs sm:text-sm text-muted-foreground">
        <span class="font-[var(--font-mono)]">{total.toLocaleString()}</span> result{total !== 1 ? "s" : ""}
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" size="sm" onclick={() => onPageChange(page - 1)} disabled={page <= 1}>
          Previous
        </Button>
        <span class="text-xs sm:text-sm text-muted-foreground font-[var(--font-mono)]">
          Page {page} of {totalPages}
        </span>
        <Button variant="outline" size="sm" onclick={() => onPageChange(page + 1)} disabled={page >= totalPages}>
          Next
        </Button>
      </div>
    </div>

    {#if selectedBillId !== null}
      {#await import("./BriefingPanel.svelte") then { default: BriefingPanel }}
        <BriefingPanel billId={selectedBillId} onClose={() => (selectedBillId = null)} />
      {/await}
    {/if}
  </div>
{/if}
