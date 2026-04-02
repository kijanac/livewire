import { useState, useEffect } from "react";
import { createCollection } from "../api";
import type { CollectionStub } from "../types";

const STORAGE_KEY = "bill_tracker_collections";

function loadStubs(): CollectionStub[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveStubs(stubs: CollectionStub[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stubs));
}

export function addStubToStorage(stub: CollectionStub) {
  const stubs = loadStubs();
  if (!stubs.find((s) => s.slug === stub.slug)) {
    stubs.unshift(stub);
    saveStubs(stubs);
  }
}

export function removeStubFromStorage(slug: string) {
  const stubs = loadStubs().filter((s) => s.slug !== slug);
  saveStubs(stubs);
}

export function getCollectionName(slug: string): string | null {
  const stubs = loadStubs();
  return stubs.find((s) => s.slug === slug)?.name ?? null;
}

export function useCollectionStubs() {
  const [stubs, setStubs] = useState<CollectionStub[]>(loadStubs);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const refresh = () => setStubs(loadStubs());
    window.addEventListener("hashchange", refresh);
    return () => window.removeEventListener("hashchange", refresh);
  }, []);

  const create = async (name: string) => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const collection = await createCollection({ name: name.trim() });
      const stub = { slug: collection.slug, name: collection.name };
      addStubToStorage(stub);
      setStubs(loadStubs());
      window.location.hash = `#/collection/${collection.slug}`;
    } catch {
      // Creation failure
    } finally {
      setCreating(false);
    }
  };

  return { stubs, creating, create };
}
