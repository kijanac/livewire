import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { CoalitionBrief } from "@/types";

interface BriefingCoalitionProps {
  coalition: CoalitionBrief | null;
}

export function BriefingCoalition({ coalition }: BriefingCoalitionProps) {
  if (!coalition) return null;
  if (
    coalition.ally_cities.length === 0 &&
    coalition.contested_cities.length === 0 &&
    !coalition.insight
  ) {
    return null;
  }
  return (
    <>
      <div className="animate-fade-up p-4 sm:p-6 bg-accent/5 border-l-4 border-accent" style={{ animationDelay: "450ms" }}>
        <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-3">
          Coalition Intel
        </h4>

        {coalition.ally_cities.length > 0 && (
          <div className="mb-3">
            <span className="text-xs font-medium text-green-600 dark:text-green-400">
              Allies (passed similar bills)
            </span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {coalition.ally_cities.map((city) => (
                <Badge
                  key={city}
                  variant="secondary"
                  className="bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20"
                >
                  {city}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {coalition.contested_cities.length > 0 && (
          <div className="mb-3">
            <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
              In play (still deciding)
            </span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {coalition.contested_cities.map((city) => (
                <Badge
                  key={city}
                  variant="secondary"
                  className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20"
                >
                  {city}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {coalition.insight && (
          <div className="mt-3 p-3 rounded-md bg-accent/10 border border-accent/20">
            <p className="text-sm text-foreground leading-relaxed">{coalition.insight}</p>
          </div>
        )}
      </div>
      <Separator />
    </>
  );
}
