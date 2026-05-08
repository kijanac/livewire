import type { Bill } from "../types";
import { useBillSearch } from "../hooks/useBillSearch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "./Spinner";
import { formatTopic } from "@/lib/bill-utils";
import { Search } from "lucide-react";

interface AddBillModalProps {
  existingBillIds: Set<number>;
  onAdd: (bill: Bill) => void;
  onClose: () => void;
}

function AddBillModal({ existingBillIds, onAdd, onClose }: AddBillModalProps) {
  const { search, setSearch, results, loading } = useBillSearch();

  return (
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Add Bills</DialogTitle>
        </DialogHeader>

        <div className="py-3 border-b border-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" aria-hidden="true" />
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
              <Spinner size={20} className="text-primary" />
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
