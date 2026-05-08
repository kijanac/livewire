<script lang="ts">
  import { createCollectionStore } from "@/hooks/use-collection.svelte";
  import { useErrorToast } from "@/hooks/use-error-toast.svelte";
  import AddBillModal from "./components/AddBillModal.svelte";
  import type { Bill } from "@/types";
  import { Card, CardContent } from "@/components/ui/card";
  import { Badge } from "@/components/ui/badge";
  import { Button } from "@/components/ui/button";
  import { Input } from "@/components/ui/input";
  import { cn } from "@/lib/utils";
  import { formatDate, formatTopic, getStatusClasses } from "@/lib/bill-utils";
  import Plus from "@lucide/svelte/icons/plus";
  import Share2 from "@lucide/svelte/icons/share-2";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import X from "@lucide/svelte/icons/x";

  let { slug }: { slug?: string } = $props();

  const store = createCollectionStore(slug ?? "");
  useErrorToast(store.error, "Failed to load collection");
  useErrorToast(store.mutationError, "Failed to save changes");

  // Flat edit state — Svelte 5 discriminated unions don't narrow in templates (issue #12150)
  let editingName = $state(false);
  let editNameValue = $state("");
  let editingDesc = $state(false);
  let editDescValue = $state("");
  let editingNote = $state<{ itemId: number; value: string } | null>(null);
  let showAddModal = $state(false);
  let copied = $state(false);

  function handleSaveName() {
    editingName = false;
    store.saveName(editNameValue);
  }

  function handleSaveDesc() {
    editingDesc = false;
    store.saveDescription(editDescValue);
  }

  function handleSaveNote() {
    if (!editingNote) return;
    const { itemId, value } = editingNote;
    editingNote = null;
    store.saveNote(itemId, value);
  }

  function startEditName() {
    if (store.collection) {
      editNameValue = store.collection.name;
      editingName = true;
    }
  }

  function startEditDesc() {
    if (store.collection) {
      editDescValue = store.collection.description || "";
      editingDesc = true;
    }
  }

  function startEditNote(itemId: number, currentNote: string) {
    editingNote = { itemId, value: currentNote };
  }

  function handleShare() {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }
</script>

{#if store.loading}
  <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="animate-pulse motion-reduce:animate-none">
      <div class="h-8 bg-muted rounded w-1/3 mb-4" />
      <div class="h-4 bg-muted rounded w-1/2 mb-8" />
      <div class="space-y-4">
        {#each [1, 2, 3] as i}
          <Card>
            <CardContent class="p-6">
              <div class="h-4 bg-muted rounded w-3/4 mb-2" />
              <div class="h-3 bg-muted rounded w-1/2" />
            </CardContent>
          </Card>
        {/each}
      </div>
    </div>
  </main>
{:else if store.error || !store.collection}
  <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <Card>
      <CardContent class="p-12 text-center">
        <p class="text-muted-foreground">{store.error || "This collection doesn't exist or was deleted."}</p>
        <a href="#" class="text-primary hover:text-primary/80 text-sm mt-2 inline-block">Back to dashboard</a>
      </CardContent>
    </Card>
  </main>
{:else}
  {@const collection = store.collection}
  {@const existingBillIds = new Set(collection.items.map((i) => i.bill_id))}

  <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
        <div class="flex-1">
          {#if editingName}
            <Input
              type="text"
              bind:value={editNameValue}
              onblur={handleSaveName}
              onkeydown={(e) => {
                if (e.key === "Enter") handleSaveName();
                else if (e.key === "Escape") editingName = false;
              }}
              autofocus
              class="text-2xl font-bold text-foreground bg-transparent border-b-2 border-primary outline-none w-full"
            />
          {:else}
            <h1 class="text-page-heading uppercase tracking-tight">
              <button type="button" class="hover:text-primary transition-colors text-left"
                onclick={startEditName}
                aria-label="Edit collection name">{collection.name}</button>
            </h1>
          {/if}

          {#if editingDesc}
            <textarea
              bind:value={editDescValue}
              onblur={handleSaveDesc}
              onkeydown={(e) => {
                if (e.key === "Escape") editingDesc = false;
              }}
              autofocus
              rows={2}
              class="mt-1 text-sm text-muted-foreground bg-transparent border border-border rounded-lg outline-none w-full px-2 py-1 focus:ring-2 focus:ring-primary"
              placeholder="What's this collection for?"
            />
          {:else}
            <button type="button" class="mt-1 text-sm text-muted-foreground hover:text-foreground transition-colors text-left"
              onclick={startEditDesc}
              aria-label="Edit description">{collection.description || "What's this collection for?"}</button>
          {/if}
        </div>

        <div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          <Button variant="outline" onclick={handleShare} class="inline-flex items-center gap-1.5">
            <Share2 class="h-4 w-4" /> {copied ? "Copied!" : "Share"}
          </Button>
          <Button onclick={() => (showAddModal = true)} class="inline-flex items-center gap-1.5">
            <Plus class="h-4 w-4" /> Add Bills
          </Button>
          <Button variant="destructive" size="icon" onclick={() => store.remove()} title="Delete collection" aria-label="Delete collection">
            <Trash2 class="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div class="mt-2 text-xs font-[var(--font-mono)] text-muted-foreground">
        {collection.items.length} bill{collection.items.length !== 1 ? "s" : ""} in collection
      </div>
    </div>

    <!-- Items -->
    {#if collection.items.length === 0}
      <Card>
        <CardContent class="p-12 text-center">
          <p class="text-muted-foreground">This collection is empty.</p>
          <Button variant="link" onclick={() => (showAddModal = true)} class="mt-3 text-sm">
            Search and add bills to get started
          </Button>
        </CardContent>
      </Card>
    {:else}
      <div class="space-y-3">
        {#each collection.items as item (item.id)}
          {@const bill = item.bill}
          {@const isEditingNote = editingNote?.itemId === item.id}

          <Card class={cn(
            "overflow-hidden py-0 gap-0",
            bill.urgency === "urgent" ? "border-l-4 border-l-primary" : bill.urgency === "soon" ? "border-l-4 border-l-accent" : ""
          )}>
            <CardContent class="p-4">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs font-medium text-muted-foreground">{bill.city_name}, {bill.state}</span>
                    {#if bill.file_number}
                      <span class="text-xs text-muted-foreground font-[var(--font-mono)]">{bill.file_number}</span>
                    {/if}
                    {#if bill.urgency === "urgent"}
                      <Badge class="bg-primary text-primary-foreground">This Week</Badge>
                    {:else if bill.urgency === "soon"}
                      <Badge variant="secondary">Upcoming</Badge>
                    {/if}
                  </div>
                  <p class="text-sm font-medium text-foreground">{bill.title}</p>
                  <div class="flex items-center gap-2 mt-1.5">
                    {#if bill.status}
                      <Badge class={getStatusClasses(bill.status)}>{bill.status}</Badge>
                    {/if}
                    {#if bill.type_name}
                      <span class="text-xs text-muted-foreground">{bill.type_name}</span>
                    {/if}
                    {#if bill.intro_date}
                      <span class="text-xs font-[var(--font-mono)] text-muted-foreground">Introduced {formatDate(bill.intro_date)}</span>
                    {/if}
                    {#if bill.url}
                      <a href={bill.url} target="_blank" rel="noopener noreferrer" class="text-xs text-primary hover:text-primary/80 transition-colors">View legislation</a>
                    {/if}
                  </div>
                  {#if bill.topics.length > 0}
                    <div class="flex flex-wrap gap-1 mt-1.5">
                      {#each bill.topics as topic}
                        <Badge variant="secondary">{formatTopic(topic)}</Badge>
                      {/each}
                    </div>
                  {/if}
                </div>
                <Button variant="ghost" size="icon-sm" onclick={() => store.removeItem(item.id)}
                  class="flex-shrink-0 text-muted-foreground hover:text-destructive" title="Remove from collection">
                  <X class="h-4 w-4" />
                </Button>
              </div>
            </CardContent>

            <!-- Note section -->
            <div class="bg-accent/10 border-t border-accent/20 px-4 py-2.5">
              {#if isEditingNote}
                <textarea
                  bind:value={editingNote.value}
                  onblur={handleSaveNote}
                  onkeydown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSaveNote();
                    } else if (e.key === "Escape") {
                      editingNote = null;
                    }
                  }}
                  autofocus
                  rows={2}
                  placeholder="Who to contact, what to do next, coalition notes..."
                  class="w-full bg-transparent text-sm text-foreground placeholder-muted-foreground outline-none resize-none"
                />
              {:else}
                <button type="button" class="text-sm text-foreground hover:text-primary transition-colors min-h-[1.25rem] text-left w-full"
                  onclick={() => startEditNote(item.id, item.note || "")}
                  aria-label="Edit note">
                  {#if item.note}
                    {item.note}
                  {:else}
                    <span class="text-muted-foreground italic">Add a note — contacts, next steps, strategy...</span>
                  {/if}
                </button>
              {/if}
            </div>
          </Card>
        {/each}
      </div>
    {/if}

    {#if showAddModal}
      <AddBillModal
        existingBillIds={existingBillIds}
        onAdd={(bill: Bill) => { store.addBill(bill); }}
        onClose={() => (showAddModal = false)}
      />
    {/if}
  </main>
{/if}
