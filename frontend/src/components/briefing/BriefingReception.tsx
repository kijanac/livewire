import { Separator } from "@/components/ui/separator";

interface BriefingReceptionProps {
  reception: string | null;
}

export function BriefingReception({ reception }: BriefingReceptionProps) {
  if (!reception) return null;
  return (
    <>
      <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "350ms" }}>
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
          Public Reception
        </h4>
        <p className="text-sm text-foreground leading-relaxed">{reception}</p>
      </div>
      <Separator />
    </>
  );
}
