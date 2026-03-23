import { useState, useEffect } from "react";
import { createCollection } from "../api";
import type { CollectionStub } from "../types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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

function CollectionsSidebar() {
  const [stubs, setStubs] = useState<CollectionStub[]>(loadStubs);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  // Re-read localStorage when the component mounts or the hash changes
  useEffect(() => {
    const refresh = () => setStubs(loadStubs());
    window.addEventListener("hashchange", refresh);
    return () => window.removeEventListener("hashchange", refresh);
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const collection = await createCollection({ name: newName.trim() });
      const stub = { slug: collection.slug, name: collection.name };
      addStubToStorage(stub);
      setStubs(loadStubs());
      setNewName("");
      window.location.hash = `#/collection/${collection.slug}`;
    } catch {
      // Creation failure
    } finally {
      setCreating(false);
    }
  };

  return (
    <Card className="mb-6 border-l-2 border-l-primary">
      <CardContent>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-foreground uppercase tracking-wider">
            Collections
          </h2>
        </div>

        <div className="flex gap-2 mb-3">
          <Input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            placeholder="Name this collection..."
            className="flex-1"
          />
          <Button
            onClick={handleCreate}
            disabled={creating || !newName.trim()}
          >
            {creating ? "..." : "Create"}
          </Button>
        </div>

        {stubs.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            No collections yet. Name one above to start tracking.
          </p>
        ) : (
          <ul className="space-y-1">
            {stubs.map((stub) => (
              <li key={stub.slug}>
                <a
                  href={`#/collection/${stub.slug}`}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  <svg
                    className="h-4 w-4 text-primary flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z"
                    />
                  </svg>
                  <span className="truncate">{stub.name}</span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default CollectionsSidebar;
