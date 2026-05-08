import { useBriefing } from "@/hooks/useBriefing";
import { useErrorToast } from "@/hooks/useErrorToast";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "../Spinner";
import { formatTopic, getStatusClasses } from "@/lib/bill-utils";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { BriefingSummary } from "./BriefingSummary";
import { BriefingPower } from "./BriefingPower";
import { BriefingOrganizing } from "./BriefingOrganizing";
import { BriefingReception } from "./BriefingReception";
import { BriefingNarrative } from "./BriefingNarrative";
import { BriefingTimeline } from "./BriefingTimeline";
import { BriefingDocuments } from "./BriefingDocuments";
import { BriefingNews } from "./BriefingNews";
import { BriefingSimilar } from "./BriefingSimilar";
import { BriefingCoalition } from "./BriefingCoalition";
import { BriefingNotes } from "./BriefingNotes";

interface BriefingShellProps {
  billId: number;
  onClose: () => void;
  onNavigate?: (billId: number) => void;
}

export function BriefingShell({ billId, onClose, onNavigate }: BriefingShellProps) {
  const { history, briefing, loading, error, navigateTo, goBack } = useBriefing(billId);
  useErrorToast(error, "Failed to load briefing");

  const handleNavigate = (id: number) => {
    navigateTo(id);
    onNavigate?.(id);
  };

  return (
    <Sheet open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-hidden flex flex-col">
        <SheetHeader className="flex-shrink-0">
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <Button variant="ghost" size="icon-sm" onClick={goBack} title="Previous bill">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            )}
            <SheetTitle>Intel Briefing</SheetTitle>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto overscroll-contain">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Spinner size={24} className="text-primary" />
              <span className="text-sm text-muted-foreground">Building briefing...</span>
            </div>
          )}

          {error && (
            <div className="p-4 sm:p-6">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {!loading && briefing && (
            <div>
              <div className="animate-fade-up p-4 sm:p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-muted-foreground">
                    {briefing.bill.city_name}, {briefing.bill.state}
                  </span>
                  {briefing.bill.file_number && (
                    <span className="text-xs text-muted-foreground font-[var(--font-mono)]">
                      {briefing.bill.file_number}
                    </span>
                  )}
                  {briefing.bill.urgency === "urgent" && (
                    <Badge className="bg-primary text-primary-foreground">This Week</Badge>
                  )}
                  {briefing.bill.urgency === "soon" && (
                    <Badge variant="secondary">This Month</Badge>
                  )}
                </div>
                <h3 className="text-section-heading text-foreground mb-2">
                  {briefing.bill.title}
                </h3>
                <div className="flex flex-wrap items-center gap-2">
                  {briefing.bill.status && (
                    <Badge className={getStatusClasses(briefing.bill.status)}>
                      {briefing.bill.status}
                    </Badge>
                  )}
                  {briefing.bill.topics.map((t) => (
                    <Badge key={t} variant="secondary">
                      {formatTopic(t)}
                    </Badge>
                  ))}
                </div>
                {briefing.bill.url && (
                  <a
                    href={briefing.bill.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80 mt-2"
                  >
                    Read full legislation
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>

              <Separator />

              <BriefingSummary summary={briefing.summary} impact={briefing.impact} />
              <BriefingPower power={briefing.power} />
              <BriefingOrganizing organizing={briefing.organizing} />
              <BriefingReception reception={briefing.reception} />
              <BriefingNarrative narrative={briefing.narrative} />
              <BriefingTimeline timeline={briefing.timeline} />
              <BriefingDocuments documents={briefing.documents} />
              <BriefingNews news={briefing.news} />
              <BriefingSimilar similarBills={briefing.similar_bills} onNavigate={handleNavigate} />
              <BriefingCoalition coalition={briefing.coalition} />
              <BriefingNotes notes={briefing.collection_notes} />
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
