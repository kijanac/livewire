import { useState, useEffect, useCallback } from "react";
import {
  fetchCollection,
  updateCollection,
  deleteCollection,
  addBillToCollection,
  updateCollectionItem,
  removeBillFromCollection,
} from "../api";
import type { Collection, Bill } from "../types";
import { addStubToStorage, removeStubFromStorage } from "./useCollectionStubs";

export function useCollection(slug: string) {
  const [collection, setCollection] = useState<Collection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCollection(slug);
      setCollection(data);
      addStubToStorage({ slug: data.slug, name: data.name });
    } catch {
      setError("This collection doesn't exist or was deleted.");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    load();
  }, [load]);

  const saveName = async (name: string) => {
    if (!collection || !name.trim()) return;
    try {
      const updated = await updateCollection(slug, { name: name.trim() });
      setCollection(updated);
      addStubToStorage({ slug: updated.slug, name: updated.name });
    } catch { /* ignore */ }
  };

  const saveDescription = async (description: string) => {
    if (!collection) return;
    try {
      const updated = await updateCollection(slug, { description: description.trim() || undefined });
      setCollection(updated);
    } catch { /* ignore */ }
  };

  const addBill = async (bill: Bill) => {
    if (!collection) return;
    try {
      await addBillToCollection(slug, bill.id);
      await load();
    } catch { /* ignore */ }
  };

  const saveNote = async (itemId: number, note: string) => {
    try {
      await updateCollectionItem(slug, itemId, note);
      await load();
    } catch { /* ignore */ }
  };

  const removeItem = async (itemId: number) => {
    try {
      await removeBillFromCollection(slug, itemId);
      await load();
    } catch { /* ignore */ }
  };

  const remove = async () => {
    if (!collection) return false;
    if (!confirm("Delete this collection and all its notes? This can't be undone.")) return false;
    try {
      await deleteCollection(slug);
      removeStubFromStorage(slug);
      window.location.hash = "";
      return true;
    } catch {
      return false;
    }
  };

  return {
    collection,
    loading,
    error,
    saveName,
    saveDescription,
    addBill,
    saveNote,
    removeItem,
    remove,
  };
}
