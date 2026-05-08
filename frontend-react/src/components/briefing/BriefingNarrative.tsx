import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { TrendingUp } from "lucide-react";
import type { NarrativeSection } from "@/types";

interface BriefingNarrativeProps {
  narrative: NarrativeSection | null;
}

export function BriefingNarrative({ narrative }: BriefingNarrativeProps) {
  if (!narrative) return null;
  if (narrative.frames.length === 0 && narrative.talking_points.length === 0) return null;

  return (
    <>
      <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "400ms" }}>
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Narrative Analysis
        </h4>

        {narrative.frames.length > 0 && (
          <div className="mb-4">
            <span className="text-xs font-medium text-muted-foreground">Media Framing</span>
            <div className="mt-1.5 space-y-1.5">
              {narrative.frames.map((f, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span
                    className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${
                      f.stance === "support"
                        ? "bg-green-500"
                        : f.stance === "opposition"
                        ? "bg-red-500"
                        : "bg-muted-foreground/40"
                    }`}
                  />
                  <div className="min-w-0">
                    <p className="text-sm text-foreground line-clamp-2">{f.headline}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-muted-foreground">{f.source}</span>
                      <Badge variant="secondary" className="text-[10px] px-1 py-0">
                        {f.frame}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          {narrative.support_narrative && (
            <div className="p-3 rounded-md bg-green-500/5 border border-green-500/10">
              <span className="text-xs font-medium text-green-600 dark:text-green-400">Support Frame</span>
              <p className="text-sm text-foreground leading-relaxed mt-1">
                {narrative.support_narrative}
              </p>
            </div>
          )}
          {narrative.opposition_narrative && (
            <div className="p-3 rounded-md bg-red-500/5 border border-red-500/10">
              <span className="text-xs font-medium text-red-600 dark:text-red-400">Opposition Frame</span>
              <p className="text-sm text-foreground leading-relaxed mt-1">
                {narrative.opposition_narrative}
              </p>
            </div>
          )}
        </div>

        {narrative.narrative_trajectory && (
          <div className="mt-3 flex items-start gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
            <p className="text-xs text-muted-foreground leading-relaxed">
              {narrative.narrative_trajectory}
            </p>
          </div>
        )}

        {narrative.talking_points.length > 0 && (
          <div className="mt-4 p-3 rounded-md bg-primary/5 border border-primary/10">
            <span className="text-xs font-bold text-primary uppercase tracking-wider">
              Talking Points
            </span>
            <ul className="mt-2 space-y-1.5">
              {narrative.talking_points.map((tp, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-foreground leading-relaxed">
                  <span className="text-primary font-bold mt-px">&bull;</span>
                  {tp}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <Separator />
    </>
  );
}
