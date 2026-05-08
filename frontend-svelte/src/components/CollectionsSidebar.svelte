<script lang="ts">
  import { createCollectionStubs } from "@/hooks/use-collection-stubs.svelte";
  import { Card, CardContent } from "@/components/ui/card";
  import { Button } from "@/components/ui/button";
  import { Input } from "@/components/ui/input";

  const { stubs, creating, create } = createCollectionStubs();
  let newName = $state("");

  function handleCreate() {
    create(newName);
    newName = "";
  }
</script>

<Card class="mb-6 border-l-2 border-l-primary">
  <CardContent>
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-sm font-bold text-foreground uppercase tracking-wider">Collections</h2>
    </div>

    <div class="flex gap-2 mb-3">
      <Input
        type="text"
        bind:value={newName}
        onkeydown={(e) => e.key === "Enter" && handleCreate()}
        placeholder="Name this collection..."
        class="flex-1"
      />
      <Button onclick={handleCreate} disabled={creating || !newName.trim()}>
        {creating ? "..." : "Create"}
      </Button>
    </div>

    {#if stubs.length === 0}
      <p class="text-xs text-muted-foreground">
        No collections yet. Name one above to start tracking.
      </p>
    {:else}
      <ul class="space-y-1">
        {#each stubs as stub (stub.slug)}
          <li>
            <a
              href={`#/collection/${stub.slug}`}
              class="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm font-medium text-foreground hover:text-primary transition-colors"
            >
              <svg class="h-4 w-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
              </svg>
              <span class="truncate">{stub.name}</span>
            </a>
          </li>
        {/each}
      </ul>
    {/if}
  </CardContent>
</Card>
