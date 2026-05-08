import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { getStatusClasses } from "@/lib/bill-utils";
import type { SimilarBill } from "@/types";

interface BriefingSimilarProps {
  similarBills: SimilarBill[];
  onNavigate: (id: number) => void;
}

export function BriefingSimilar({ similarBills, onNavigate }: BriefingSimilarProps) {
  if (similarBills.length === 0) return null;
  return (
    <>
      <div className="p-4 sm:p-6">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Same Fight, Other Cities
        </h4>
        <div className="space-y-2">
          {similarBills.map((b) => (
            <Button
              key={b.id}
              variant="outline"
              onClick={() => onNavigate(b.id)}
              className="w-full text-left h-auto p-3 justify-start items-start flex-col hover:border-primary transition-colors cursor-pointer whitespace-normal"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-muted-foreground">
                  {b.city_name}, {b.state}
                </span>
                {b.file_number && (
                  <span className="text-xs text-muted-foreground font-[var(--font-mono)]">
                    {b.file_number}
                  </span>
                )}
                {b.status && <Badge className={getStatusClasses(b.status)}>{b.status}</Badge>}
              </div>
              <p className="text-sm text-foreground line-clamp-2">{b.title}</p>
            </Button>
          ))}
        </div>
      </div>
      <Separator />
    </>
  );
}
