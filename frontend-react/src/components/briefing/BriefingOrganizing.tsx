import { Separator } from "@/components/ui/separator";

interface BriefingOrganizingProps {
  organizing: string | null;
}

export function BriefingOrganizing({ organizing }: BriefingOrganizingProps) {
  if (!organizing) return null;
  return (
    <>
      <div className="animate-fade-up p-4 sm:p-6 bg-accent/10 border-l-4 border-accent" style={{ animationDelay: "275ms" }}>
        <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-2">
          Organizing Activity
        </h4>
        <p className="text-sm text-foreground leading-relaxed">{organizing}</p>
      </div>
      <Separator />
    </>
  );
}
