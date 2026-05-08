import { Separator } from "@/components/ui/separator";
import { formatDate } from "@/lib/bill-utils";

interface BriefingTimelineProps {
  timeline: { event: string; date: string }[];
}

export function BriefingTimeline({ timeline }: BriefingTimelineProps) {
  if (timeline.length === 0) return null;
  return (
    <>
      <div className="p-4 sm:p-6">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Timeline
        </h4>
        <div className="space-y-2">
          {timeline.map((event, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
              <span className="text-sm text-foreground font-medium">{event.event}</span>
              <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                {formatDate(event.date)}
              </span>
            </div>
          ))}
        </div>
      </div>
      <Separator />
    </>
  );
}
