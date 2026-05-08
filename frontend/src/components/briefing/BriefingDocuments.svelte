<script lang="ts">
  import { Separator } from "@/components/ui/separator";
  import FileText from "@lucide/svelte/icons/file-text";
  import type { BillDocument } from "@/types";

  let { documents }: { documents: BillDocument[] } = $props();
</script>

{#if documents.length > 0}
  <div class="p-4 sm:p-6">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Documents</h4>
    <div class="space-y-2">
      {#each documents as doc (doc.id)}
        <a href={doc.url} target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 group">
          <FileText class="h-4 w-4 text-muted-foreground group-hover:text-primary flex-shrink-0" />
          <span class="text-sm text-foreground group-hover:text-primary transition-colors truncate">{doc.name}</span>
        </a>
      {/each}
    </div>
  </div>
  <Separator />
{/if}
