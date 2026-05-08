import {
  fetchCollection,
  updateCollection,
  deleteCollection,
  addBillToCollection,
  updateCollectionItem,
  removeBillFromCollection,
} from "@/api";
import type { Collection, Bill } from "@/types";
import { addStubToStorage, removeStubFromStorage } from "./use-collection-stubs.svelte";

export function createCollectionStore(slug: string) {
  let collection = $state<Collection | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let mutationError = $state<string | null>(null);

  async function reload(signal?: AbortSignal) {
    const data = await fetchCollection(slug, signal);
    collection = data;
    addStubToStorage({ slug: data.slug, name: data.name });
    return data;
  }

  $effect(() => {
    const ctrl = new AbortController();
    loading = true;
    error = null;
    reload(ctrl.signal)
      .catch((err) => {
        if (err.name !== "AbortError") {
          error = "This collection doesn't exist or was deleted.";
        }
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  async function saveName(name: string) {
    if (!collection || !name.trim()) return;
    mutationError = null;
    try {
      const updated = await updateCollection(slug, { name: name.trim() });
      collection = updated;
      addStubToStorage({ slug: updated.slug, name: updated.name });
    } catch (err) {
      mutationError = err instanceof Error ? err.message : String(err);
    }
  }

  async function saveDescription(description: string) {
    if (!collection) return;
    mutationError = null;
    try {
      const updated = await updateCollection(slug, {
        description: description.trim() || undefined,
      });
      collection = updated;
    } catch (err) {
      mutationError = err instanceof Error ? err.message : String(err);
    }
  }

  async function addBill(bill: Bill) {
    if (!collection) return;
    mutationError = null;
    try {
      await addBillToCollection(slug, bill.id);
      await reload();
    } catch (err) {
      mutationError = err instanceof Error ? err.message : String(err);
    }
  }

  async function saveNote(itemId: number, note: string) {
    mutationError = null;
    try {
      await updateCollectionItem(slug, itemId, note);
      await reload();
    } catch (err) {
      mutationError = err instanceof Error ? err.message : String(err);
    }
  }

  async function removeItem(itemId: number) {
    mutationError = null;
    try {
      await removeBillFromCollection(slug, itemId);
      await reload();
    } catch (err) {
      mutationError = err instanceof Error ? err.message : String(err);
    }
  }

  async function remove() {
    if (!collection) return false;
    if (!confirm("Delete this collection and all its notes? This can't be undone.")) return false;
    mutationError = null;
    try {
      await deleteCollection(slug);
      removeStubFromStorage(slug);
      window.location.hash = "";
      return true;
    } catch (err) {
      mutationError = err instanceof Error ? err.message : String(err);
      return false;
    }
  }

  return {
    get collection() { return collection; },
    get loading() { return loading; },
    get error() { return error; },
    get mutationError() { return mutationError; },
    saveName,
    saveDescription,
    addBill,
    saveNote,
    removeItem,
    remove,
  };
}
