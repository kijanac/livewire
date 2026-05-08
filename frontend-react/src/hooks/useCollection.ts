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
  const [mutationError, setMutationError] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      fetchCollection(slug, signal).then((data) => {
        setCollection(data);
        addStubToStorage({ slug: data.slug, name: data.name });
        return data;
      }),
    [slug]
  );

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    reload(ctrl.signal)
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError("This collection doesn't exist or was deleted.");
        }
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [reload]);

  const saveName = async (name: string) => {
    if (!collection || !name.trim()) return;
    setMutationError(null);
    try {
      const updated = await updateCollection(slug, { name: name.trim() });
      setCollection(updated);
      addStubToStorage({ slug: updated.slug, name: updated.name });
    } catch (err) {
      setMutationError(err instanceof Error ? err.message : String(err));
    }
  };

  const saveDescription = async (description: string) => {
    if (!collection) return;
    setMutationError(null);
    try {
      const updated = await updateCollection(slug, {
        description: description.trim() || undefined,
      });
      setCollection(updated);
    } catch (err) {
      setMutationError(err instanceof Error ? err.message : String(err));
    }
  };

  const addBill = async (bill: Bill) => {
    if (!collection) return;
    setMutationError(null);
    try {
      await addBillToCollection(slug, bill.id);
      await reload();
    } catch (err) {
      setMutationError(err instanceof Error ? err.message : String(err));
    }
  };

  const saveNote = async (itemId: number, note: string) => {
    setMutationError(null);
    try {
      await updateCollectionItem(slug, itemId, note);
      await reload();
    } catch (err) {
      setMutationError(err instanceof Error ? err.message : String(err));
    }
  };

  const removeItem = async (itemId: number) => {
    setMutationError(null);
    try {
      await removeBillFromCollection(slug, itemId);
      await reload();
    } catch (err) {
      setMutationError(err instanceof Error ? err.message : String(err));
    }
  };

  const remove = async () => {
    if (!collection) return false;
    if (!confirm("Delete this collection and all its notes? This can't be undone.")) return false;
    setMutationError(null);
    try {
      await deleteCollection(slug);
      removeStubFromStorage(slug);
      window.location.hash = "";
      return true;
    } catch (err) {
      setMutationError(err instanceof Error ? err.message : String(err));
      return false;
    }
  };

  return {
    collection,
    loading,
    error,
    mutationError,
    saveName,
    saveDescription,
    addBill,
    saveNote,
    removeItem,
    remove,
  };
}
