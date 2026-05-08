import { Separator } from "@/components/ui/separator";
import { FileText } from "lucide-react";
import type { BillDocument } from "@/types";

interface BriefingDocumentsProps {
  documents: BillDocument[];
}

export function BriefingDocuments({ documents }: BriefingDocumentsProps) {
  if (documents.length === 0) return null;
  return (
    <>
      <div className="p-4 sm:p-6">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Documents
        </h4>
        <div className="space-y-2">
          {documents.map((doc) => (
            <a
              key={doc.id}
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 group"
            >
              <FileText className="h-4 w-4 text-muted-foreground group-hover:text-primary flex-shrink-0" />
              <span className="text-sm text-foreground group-hover:text-primary transition-colors truncate">
                {doc.name}
              </span>
            </a>
          ))}
        </div>
      </div>
      <Separator />
    </>
  );
}
