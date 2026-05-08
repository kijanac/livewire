interface BriefingNotesProps {
  notes: { collection_name: string; note: string }[];
}

export function BriefingNotes({ notes }: BriefingNotesProps) {
  if (notes.length === 0) return null;
  return (
    <div className="p-4 sm:p-6 bg-muted border-l-4 border-primary">
      <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
        Organizer Notes
      </h4>
      <div className="space-y-2">
        {notes.map((note, i) => (
          <div key={i}>
            <span className="text-xs font-medium text-primary">{note.collection_name}:</span>
            <p className="text-sm text-foreground leading-relaxed mt-0.5">{note.note}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
