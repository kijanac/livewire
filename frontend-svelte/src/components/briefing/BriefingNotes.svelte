<script lang="ts">
  let { notes }: { notes: { collection_name: string; note: string }[] } = $props();
</script>

{#if notes.length > 0}
  <div class="p-4 sm:p-6 bg-muted border-l-4 border-primary">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Organizer Notes</h4>
    <div class="space-y-2">
      {#each notes as note}
        <div>
          <span class="text-xs font-medium text-primary">{note.collection_name}:</span>
          <p class="text-sm text-foreground leading-relaxed mt-0.5">{note.note}</p>
        </div>
      {/each}
    </div>
  </div>
{/if}
