import type { CollectionStub } from "@/types";
import { createCollection } from "@/api";

const STORAGE_KEY = "bill_tracker_collections";

function loadStubs(): CollectionStub[] {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error("useCollectionStubs: failed to parse storage", err);
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

export function createCollectionStubs() {
  let stubs = $state<CollectionStub[]>(loadStubs());
  let creating = $state(false);
  let error = $state<Error | null>(null);

  $effect(() => {
    const refresh = () => {
      stubs = loadStubs();
    };
    window.addEventListener("hashchange", refresh);
    return () => window.removeEventListener("hashchange", refresh);
  });

  async function create(name: string) {
    if (!name.trim()) return;
    creating = true;
    error = null;
    try {
      const collection = await createCollection({ name: name.trim() });
      const stub = { slug: collection.slug, name: collection.name };
      addStubToStorage(stub);
      stubs = loadStubs();
      window.location.hash = `#/collection/${collection.slug}`;
    } catch (err) {
      error = err instanceof Error ? err : new Error(String(err));
    } finally {
      creating = false;
    }
  }

  return {
    get stubs() { return stubs; },
    get creating() { return creating; },
    get error() { return error; },
    create,
  };
}
