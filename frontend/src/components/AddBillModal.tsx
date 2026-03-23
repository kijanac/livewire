import { useState, useEffect, useCallback } from "react";
import { fetchBills } from "../api";
import type { Bill } from "../types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatTopic } from "@/lib/bill-utils";

interface AddBillModalProps {
  existingBillIds: Set<number>;
  onAdd: (bill: Bill) => void;
  onClose: () => void;
}

function AddBillModal({ existingBillIds, onAdd, onClose }: AddBillModalProps) {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(false);

  const doSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchBills({ search: query, per_page: 20 });
      setResults(data.bills);
    } catch {
      // Search failure is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      doSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search, doSearch]);

  return (
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Add Bills</DialogTitle>
        </DialogHeader>

        <div className="py-3 border-b border-border">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
              />
            </svg>
            <Input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by keyword, city, or bill number..."
              autoFocus
              className="pl-9"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto py-3">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <svg
                className="animate-spin motion-reduce:animate-none h-5 w-5 text-primary"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            </div>
          )}

          {!loading && search.trim() && results.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              No results for "{search}"
            </p>
          )}

          {!loading && !search.trim() && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Start typing to find bills
            </p>
          )}

          {!loading && results.length > 0 && (
            <ul className="divide-y divide-border">
              {results.map((bill) => {
                const alreadyAdded = existingBillIds.has(bill.id);
                return (
                  <li
                    key={bill.id}
                    className="flex items-start justify-between gap-3 py-3"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground line-clamp-2">
                        {bill.title}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted-foreground">
                          {bill.city_name}
                        </span>
                        {bill.file_number && (
                          <span className="text-xs text-muted-foreground font-[var(--font-mono)]">
                            {bill.file_number}
                          </span>
                        )}
                        {bill.status && (
                          <span className="text-xs text-muted-foreground/70">
                            {bill.status}
                          </span>
                        )}
                      </div>
                      {bill.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {bill.topics.slice(0, 3).map((topic) => (
                            <Badge
                              key={topic}
                              variant="secondary"
                            >
                              {formatTopic(topic)}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <Button
                      onClick={() => onAdd(bill)}
                      disabled={alreadyAdded}
                      size="sm"
                      variant={alreadyAdded ? "secondary" : "default"}
                      className="flex-shrink-0"
                    >
                      {alreadyAdded ? "Added" : "Add"}
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default AddBillModal;
