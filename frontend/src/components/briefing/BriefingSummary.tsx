import { Separator } from "@/components/ui/separator";

interface BriefingSummaryProps {
  summary: string | null;
  impact: string | null;
}

export function BriefingSummary({ summary, impact }: BriefingSummaryProps) {
  if (!summary && !impact) return null;
  return (
    <>
      {summary && (
        <>
          <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "75ms" }}>
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
              Summary
            </h4>
            <p className="text-sm text-foreground leading-relaxed">{summary}</p>
          </div>
          <Separator />
        </>
      )}
      {impact && (
        <>
          <div className="animate-fade-up p-4 sm:p-6 bg-primary/5 border-l-4 border-primary" style={{ animationDelay: "150ms" }}>
            <h4 className="text-xs font-bold text-primary uppercase tracking-wider mb-2">
              Why This Matters
            </h4>
            <p className="text-sm text-foreground leading-relaxed">{impact}</p>
          </div>
          <Separator />
        </>
      )}
    </>
  );
}
