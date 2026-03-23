import { useState, lazy, Suspense } from "react";
import type { Bill } from "../types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatShortDate, daysUntil } from "@/lib/bill-utils";
const BriefingPanel = lazy(() => import("./BriefingPanel"));

interface UpcomingActionsProps {
  bills: Bill[];
  loading: boolean;
}

function UpcomingActions({ bills, loading }: UpcomingActionsProps) {
  const [selectedBillId, setSelectedBillId] = useState<number | null>(null);

  if (loading) {
    return (
      <div className="mb-6">
        <h2 className="flex items-center gap-2 text-section-heading uppercase tracking-wider text-foreground mb-3">
          <span className="inline-block w-3 h-3 bg-primary" aria-hidden="true" />
          Coming Up
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse motion-reduce:animate-none">
              <CardContent>
                <div className="h-4 bg-muted rounded w-1/3 mb-2" />
                <div className="h-3 bg-muted rounded w-full mb-1" />
                <div className="h-3 bg-muted rounded w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (bills.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      <h2 className="flex items-center gap-2 text-section-heading uppercase tracking-wider text-foreground mb-3">
        <span className="inline-block w-3 h-3 bg-primary" aria-hidden="true" />
        Coming Up
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {bills.slice(0, 6).map((bill) => {
          const days = daysUntil(bill.agenda_date);
          const isUrgent = bill.urgency === "urgent";

          return (
            <button
              key={bill.id}
              onClick={() => setSelectedBillId(bill.id)}
              className="block text-left w-full"
            >
              <Card
                className={cn(
                  "animate-fade-up transition-shadow hover:shadow-md h-full cursor-pointer",
                  isUrgent
                    ? "border-l-4 border-l-primary"
                    : "border-l-4 border-l-accent"
                )}
                style={{ animationDelay: `${bills.indexOf(bill) * 75}ms` }}
              >
                <CardContent>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-muted-foreground">
                      {bill.city_name}, {bill.state}
                    </span>
                    <Badge
                      className={cn(
                        isUrgent
                          ? "bg-primary text-primary-foreground"
                          : ""
                      )}
                      variant={isUrgent ? "default" : "secondary"}
                    >
                      {days !== null && days <= 0
                        ? "Today"
                        : days === 1
                          ? "Tomorrow"
                          : `${days} days`}
                    </Badge>
                  </div>
                  <p
                    className="text-sm font-medium text-foreground line-clamp-2 mb-1"
                    title={bill.title}
                  >
                    {bill.title}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {bill.file_number && (
                      <span className="font-[var(--font-mono)]">{bill.file_number}</span>
                    )}
                    <span>{formatShortDate(bill.agenda_date)}</span>
                  </div>
                </CardContent>
              </Card>
            </button>
          );
        })}
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

export default UpcomingActions;
