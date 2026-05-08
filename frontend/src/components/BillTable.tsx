import { useState, lazy, Suspense } from "react";
import type { Bill } from "../types";
const BriefingPanel = lazy(() => import("./BriefingPanel"));
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "./Spinner";
import { cn } from "@/lib/utils";
import { formatDate, formatTopic, getStatusClasses } from "@/lib/bill-utils";
import { ROW_STAGGER_MS, staggerDelay } from "@/lib/visual-tokens";
import { ExternalLink } from "lucide-react";

interface BillTableProps {
  bills: Bill[];
  total: number;
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  loading: boolean;
}

function BillTable({
  bills,
  total,
  page,
  perPage,
  onPageChange,
  loading,
}: BillTableProps) {
  const [selectedBillId, setSelectedBillId] = useState<number | null>(null);
  const totalPages = Math.max(1, Math.ceil(total / perPage));

  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-12 text-center">
        <div className="inline-flex items-center gap-2 text-muted-foreground">
          <Spinner size={20} />
          Loading...
        </div>
      </div>
    );
  }

  if (bills.length === 0) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-12 text-center">
        <p className="text-muted-foreground">No bills match your filters.</p>
        <p className="text-sm text-muted-foreground/70 mt-1">
          Try broadening your search or clearing a filter.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg shadow-sm overflow-hidden">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead className="px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
              Jurisdiction
            </TableHead>
            <TableHead className="px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
              Bill
            </TableHead>
            <TableHead className="px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
              Status
            </TableHead>
            <TableHead className="hidden md:table-cell px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
              Topics
            </TableHead>
            <TableHead className="hidden lg:table-cell px-2 py-2 sm:px-4 sm:py-3 text-xs uppercase tracking-wider font-bold text-muted-foreground">
              Introduced
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {bills.map((bill, i) => (
            <TableRow
              key={bill.id}
              onClick={() => setSelectedBillId(bill.id)}
              className={cn(
                "animate-fade-up cursor-pointer",
                bill.urgency === "urgent" && "border-l-4 border-l-primary",
                bill.urgency === "soon" && "border-l-4 border-l-accent"
              )}
              style={staggerDelay(i, ROW_STAGGER_MS)}
            >
              <TableCell className="px-2 py-2 sm:px-4 sm:py-3 text-sm text-foreground align-top">
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium">{bill.city_name}</span>
                    {bill.jurisdiction_level === "state" && (
                      <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">State</Badge>
                    )}
                  </div>
                  {bill.urgency === "urgent" && (
                    <Badge className="bg-primary text-primary-foreground w-fit">
                      This Week
                    </Badge>
                  )}
                  {bill.urgency === "soon" && (
                    <Badge variant="secondary" className="w-fit">
                      This Month
                    </Badge>
                  )}
                </div>
              </TableCell>
              <TableCell className="px-2 py-2 sm:px-4 sm:py-3 align-top whitespace-normal">
                {/* Title + summary + metadata consolidated */}
                <p
                  className="text-sm text-foreground line-clamp-2"
                  title={bill.title}
                >
                  {bill.title}
                </p>
                {bill.summary && (
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1 italic">
                    {bill.summary}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                  {bill.file_number && (
                    <span className="font-[var(--font-mono)]">
                      {bill.file_number}
                    </span>
                  )}
                  {bill.type_name && (
                    <span>{bill.type_name}</span>
                  )}
                  {bill.url && (
                    <a
                      href={bill.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-0.5 text-muted-foreground hover:text-primary transition-colors"
                      title="View on city council site"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </TableCell>
              <TableCell className="px-2 py-2 sm:px-4 sm:py-3 align-top">
                {bill.status ? (
                  <Badge className={getStatusClasses(bill.status)}>
                    {bill.status}
                  </Badge>
                ) : (
                  <span className="text-sm text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell className="hidden md:table-cell px-2 py-2 sm:px-4 sm:py-3 align-top">
                <div className="flex flex-wrap gap-1">
                  {bill.topics.slice(0, 3).map((topic) => (
                    <Badge key={topic} variant="secondary">
                      {formatTopic(topic)}
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell className="hidden lg:table-cell px-2 py-2 sm:px-4 sm:py-3 text-sm font-[var(--font-mono)] text-muted-foreground align-top">
                {formatDate(bill.intro_date)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <div className="flex flex-col sm:flex-row items-center justify-between border-t border-border px-4 py-3 bg-muted/50 gap-2 sm:gap-0">
        <div className="text-xs sm:text-sm text-muted-foreground">
          <span className="font-[var(--font-mono)]">{total.toLocaleString()}</span> result{total !== 1 ? "s" : ""}
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-xs sm:text-sm text-muted-foreground font-[var(--font-mono)]">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      </div>

      {selectedBillId !== null && (
        <Suspense fallback={null}>
          <BriefingPanel
            billId={selectedBillId}
            onClose={() => setSelectedBillId(null)}
          />
        </Suspense>
      )}
    </div>
  );
}

export default BillTable;
