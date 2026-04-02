import { useState } from "react";
import { useCollection } from "../hooks/useCollection";
import AddBillModal from "./AddBillModal";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { formatDate, getStatusClasses } from "@/lib/bill-utils";
import { Plus, Share2, Trash2, X } from "lucide-react";

interface CollectionViewProps {
  slug: string;
}

function CollectionView({ slug }: CollectionViewProps) {
  const {
    collection,
    loading,
    error,
    saveName,
    saveDescription,
    addBill,
    saveNote,
    removeItem,
    remove,
  } = useCollection(slug);

  const [showAddModal, setShowAddModal] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [editingDesc, setEditingDesc] = useState(false);
  const [nameValue, setNameValue] = useState("");
  const [descValue, setDescValue] = useState("");
  const [copied, setCopied] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null);
  const [noteValue, setNoteValue] = useState("");

  const handleSaveName = () => {
    setEditingName(false);
    saveName(nameValue);
  };

  const handleSaveDesc = () => {
    setEditingDesc(false);
    saveDescription(descValue);
  };

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStartEditName = () => {
    if (collection) {
      setNameValue(collection.name);
      setEditingName(true);
    }
  };

  const handleStartEditDesc = () => {
    if (collection) {
      setDescValue(collection.description || "");
      setEditingDesc(true);
    }
  };

  if (loading) {
    return (
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="animate-pulse motion-reduce:animate-none">
          <div className="h-8 bg-muted rounded w-1/3 mb-4" />
          <div className="h-4 bg-muted rounded w-1/2 mb-8" />
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="h-4 bg-muted rounded w-3/4 mb-2" />
                  <div className="h-3 bg-muted rounded w-1/2" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>
    );
  }

  if (error || !collection) {
    return (
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">{error || "This collection doesn't exist or was deleted."}</p>
            <a
              href="#"
              className="text-primary hover:text-primary/80 text-sm mt-2 inline-block"
            >
              Back to dashboard
            </a>
          </CardContent>
        </Card>
      </main>
    );
  }

  const existingBillIds = new Set(collection.items.map((i) => i.bill_id));

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
          <div className="flex-1">
            {editingName ? (
              <Input
                type="text"
                value={nameValue}
                onChange={(e) => setNameValue(e.target.value)}
                onBlur={handleSaveName}
                onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                autoFocus
                className="text-2xl font-bold text-foreground bg-transparent border-b-2 border-primary outline-none w-full"
              />
            ) : (
              <h1 className="text-page-heading uppercase tracking-tight"><button type="button" className="hover:text-primary transition-colors text-left" onClick={handleStartEditName} aria-label="Edit collection name">{collection.name}</button></h1>
            )}

            {editingDesc ? (
              <textarea
                value={descValue}
                onChange={(e) => setDescValue(e.target.value)}
                onBlur={handleSaveDesc}
                autoFocus
                rows={2}
                className="mt-1 text-sm text-muted-foreground bg-transparent border border-border rounded-lg outline-none w-full px-2 py-1 focus:ring-2 focus:ring-primary"
                placeholder="What's this collection for?"
              />
            ) : (
              <button type="button" className="mt-1 text-sm text-muted-foreground hover:text-foreground transition-colors text-left" onClick={handleStartEditDesc} aria-label="Edit description">{collection.description || "What's this collection for?"}</button>
            )}
          </div>

          <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
            <Button
              variant="outline"
              onClick={handleShare}
              className="inline-flex items-center gap-1.5"
            >
              <Share2 className="h-4 w-4" />
              {copied ? "Copied!" : "Share"}
            </Button>
            <Button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              Add Bills
            </Button>
            <Button
              variant="destructive"
              size="icon"
              onClick={remove}
              title="Delete collection"
              aria-label="Delete collection"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="mt-2 text-xs font-[var(--font-mono)] text-muted-foreground">
          {collection.items.length} bill{collection.items.length !== 1 ? "s" : ""} in collection
        </div>
      </div>

      {/* Items */}
      {collection.items.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">This collection is empty.</p>
            <Button
              variant="link"
              onClick={() => setShowAddModal(true)}
              className="mt-3 text-sm"
            >
              Search and add bills to get started
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {collection.items.map((item) => {
            const bill = item.bill;
            const isEditingNote = editingNoteId === item.id;

            return (
              <Card
                key={item.id}
                className={cn(
                  "overflow-hidden py-0 gap-0",
                  bill.urgency === "urgent"
                    ? "border-l-4 border-l-primary"
                    : bill.urgency === "soon"
                      ? "border-l-4 border-l-accent"
                      : ""
                )}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-muted-foreground">
                          {bill.city_name}, {bill.state}
                        </span>
                        {bill.file_number && (
                          <span className="text-xs text-muted-foreground font-[var(--font-mono)]">
                            {bill.file_number}
                          </span>
                        )}
                        {bill.urgency === "urgent" && (
                          <Badge className="bg-primary text-primary-foreground">
                            This Week
                          </Badge>
                        )}
                        {bill.urgency === "soon" && (
                          <Badge variant="secondary">
                            Upcoming
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm font-medium text-foreground">
                        {bill.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        {bill.status && (
                          <Badge className={getStatusClasses(bill.status)}>
                            {bill.status}
                          </Badge>
                        )}
                        {bill.type_name && (
                          <span className="text-xs text-muted-foreground">{bill.type_name}</span>
                        )}
                        {bill.intro_date && (
                          <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                            Introduced {formatDate(bill.intro_date)}
                          </span>
                        )}
                        {bill.url && (
                          <a
                            href={bill.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:text-primary/80 transition-colors"
                          >
                            View legislation
                          </a>
                        )}
                      </div>
                      {bill.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {bill.topics.map((topic) => (
                            <Badge
                              key={topic}
                              variant="secondary"
                            >
                              {topic.replace(/_/g, " ")}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => removeItem(item.id)}
                      className="flex-shrink-0 text-muted-foreground hover:text-destructive"
                      title="Remove from collection"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>

                {/* Note section */}
                <div className="bg-accent/10 border-t border-accent/20 px-4 py-2.5">
                  {isEditingNote ? (
                    <textarea
                      value={noteValue}
                      onChange={(e) => setNoteValue(e.target.value)}
                      onBlur={() => {
                        setEditingNoteId(null);
                        saveNote(item.id, noteValue);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          setEditingNoteId(null);
                          saveNote(item.id, noteValue);
                        }
                      }}
                      autoFocus
                      rows={2}
                      placeholder="Who to contact, what to do next, coalition notes..."
                      className="w-full bg-transparent text-sm text-foreground placeholder-muted-foreground outline-none resize-none"
                    />
                  ) : (
                    <button
                      type="button"
                      className="text-sm text-foreground hover:text-primary transition-colors min-h-[1.25rem] text-left w-full"
                      onClick={() => {
                        setEditingNoteId(item.id);
                        setNoteValue(item.note || "");
                      }}
                      aria-label="Edit note"
                    >
                      {item.note || (
                        <span className="text-muted-foreground italic">
                          Add a note — contacts, next steps, strategy...
                        </span>
                      )}
                    </button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {showAddModal && (
        <AddBillModal
          existingBillIds={existingBillIds}
          onAdd={(bill) => {
            addBill(bill);
          }}
          onClose={() => setShowAddModal(false)}
        />
      )}
    </main>
  );
}

export default CollectionView;
