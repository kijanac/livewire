import { useState, useEffect } from "react";
import { fetchBriefing } from "../api";
import type { BillBriefing } from "../types";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { formatDate, getStatusClasses } from "@/lib/bill-utils";

interface BriefingPanelProps {
  billId: number;
  onClose: () => void;
  onNavigate?: (billId: number) => void;
}

function BriefingPanel({ billId, onClose, onNavigate }: BriefingPanelProps) {
  const [currentBillId, setCurrentBillId] = useState(billId);
  const [history, setHistory] = useState<number[]>([]);
  const [briefing, setBriefing] = useState<BillBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchBriefing(currentBillId)
      .then(setBriefing)
      .catch(() => setError("Couldn't load this briefing. Try again."))
      .finally(() => setLoading(false));
  }, [currentBillId]);

  const navigateTo = (id: number) => {
    setHistory((prev) => [...prev, currentBillId]);
    setCurrentBillId(id);
    onNavigate?.(id);
  };

  const goBack = () => {
    const prev = history[history.length - 1];
    if (prev !== undefined) {
      setHistory((h) => h.slice(0, -1));
      setCurrentBillId(prev);
    }
  };

  return (
    <Sheet open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-hidden flex flex-col">
        <SheetHeader className="flex-shrink-0">
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={goBack}
                title="Previous bill"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
                </svg>
              </Button>
            )}
            <SheetTitle>Intel Briefing</SheetTitle>
          </div>
        </SheetHeader>

        {/* Content */}
        <div className="flex-1 overflow-y-auto overscroll-contain">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <svg className="animate-spin motion-reduce:animate-none h-6 w-6 text-primary" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
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
              {/* Bill Header */}
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
                    <Badge className="bg-primary text-primary-foreground">
                      This Week
                    </Badge>
                  )}
                  {briefing.bill.urgency === "soon" && (
                    <Badge variant="secondary">
                      This Month
                    </Badge>
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
                      {t.replace(/_/g, " ")}
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
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </a>
                )}
              </div>

              <Separator />

              {/* Summary */}
              {briefing.summary && (
                <>
                  <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "75ms" }}>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
                      Summary
                    </h4>
                    <p className="text-sm text-foreground leading-relaxed">
                      {briefing.summary}
                    </p>
                  </div>
                  <Separator />
                </>
              )}

              {/* Impact */}
              {briefing.impact && (
                <>
                  <div className="animate-fade-up p-4 sm:p-6 bg-primary/5 border-l-4 border-primary" style={{ animationDelay: "150ms" }}>
                    <h4 className="text-xs font-bold text-primary uppercase tracking-wider mb-2">
                      Why This Matters
                    </h4>
                    <p className="text-sm text-foreground leading-relaxed">
                      {briefing.impact}
                    </p>
                  </div>
                  <Separator />
                </>
              )}

              {/* Power Intelligence */}
              {briefing.power && (briefing.power.sponsors.length > 0 || briefing.power.votes || briefing.power.actions.length > 0) && (() => {
                const v = briefing.power!.votes;
                const totalVotes = v ? v.yea + v.nay + v.abstain + v.absent + v.other : 0;
                return (
                <>
                  <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "200ms" }}>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Power Map
                    </h4>

                    {briefing.power!.sponsors.length > 0 && (
                      <div className="mb-4">
                        <span className="text-xs font-medium text-muted-foreground">Sponsors</span>
                        <div className="flex flex-wrap gap-1.5 mt-1.5">
                          {briefing.power!.sponsors.map((s) => (
                            <span
                              key={s.id}
                              className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-primary/10 text-primary font-medium"
                            >
                              {s.name}
                              {s.district && (
                                <span className="text-primary/60">D{s.district}</span>
                              )}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {v && totalVotes > 0 && (
                      <div className="mb-4">
                        <span className="text-xs font-medium text-muted-foreground">Vote Breakdown</span>
                        <div className="mt-1.5">
                          <div className="flex h-3 rounded-full overflow-hidden bg-muted">
                            {v.yea > 0 && (
                              <div
                                className="bg-emerald-500"
                                style={{ width: `${(v.yea / totalVotes) * 100}%` }}
                                title={`Yea: ${v.yea}`}
                              />
                            )}
                            {v.nay > 0 && (
                              <div
                                className="bg-red-500"
                                style={{ width: `${(v.nay / totalVotes) * 100}%` }}
                                title={`Nay: ${v.nay}`}
                              />
                            )}
                            {(v.abstain + v.absent + v.other) > 0 && (
                              <div
                                className="bg-muted-foreground/30"
                                style={{ width: `${((v.abstain + v.absent + v.other) / totalVotes) * 100}%` }}
                                title={`Other: ${v.abstain + v.absent + v.other}`}
                              />
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                            {v.yea > 0 && (
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                                Yea {v.yea}
                              </span>
                            )}
                            {v.nay > 0 && (
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-red-500" />
                                Nay {v.nay}
                              </span>
                            )}
                            {v.abstain > 0 && (
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-muted-foreground/30" />
                                Abstain {v.abstain}
                              </span>
                            )}
                            {v.absent > 0 && (
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-muted-foreground/30" />
                                Absent {v.absent}
                              </span>
                            )}
                          </div>
                          {v.records.length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-primary cursor-pointer hover:text-primary/80">
                                Show individual votes ({v.records.length})
                              </summary>
                              <div className="mt-1.5 grid grid-cols-2 gap-1">
                                {v.records.map((r, i) => (
                                  <div key={i} className="flex items-center gap-1.5 text-xs">
                                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                      r.vote === "yea" ? "bg-emerald-500" :
                                      r.vote === "nay" ? "bg-red-500" :
                                      "bg-muted-foreground/30"
                                    }`} />
                                    <span className="text-foreground truncate">{r.official}</span>
                                  </div>
                                ))}
                              </div>
                            </details>
                          )}
                        </div>
                      </div>
                    )}

                    {briefing.power!.actions.length > 0 && (
                      <div className="mb-4">
                        <span className="text-xs font-medium text-muted-foreground">Action History</span>
                        <div className="mt-1.5 space-y-1.5">
                          {briefing.power!.actions.slice(-8).map((a, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 mt-1.5 flex-shrink-0" />
                              <div className="min-w-0">
                                <span className="text-xs text-foreground">{a.action || "Action"}</span>
                                <div className="flex items-center gap-2">
                                  {a.date && (
                                    <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                                      {formatDate(a.date)}
                                    </span>
                                  )}
                                  {a.body && (
                                    <span className="text-xs text-muted-foreground">{a.body}</span>
                                  )}
                                  {a.result && (
                                    <Badge variant="secondary" className="text-[10px] px-1 py-0">
                                      {a.result}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {briefing.power!.analysis && (
                      <div className="mt-3 p-3 rounded-md bg-primary/5 border border-primary/10">
                        <p className="text-sm text-foreground leading-relaxed">
                          {briefing.power!.analysis}
                        </p>
                      </div>
                    )}
                  </div>
                  <Separator />
                </>
                );
              })()}

              {/* Organizing Activity */}
              {briefing.organizing && (
                <>
                  <div className="animate-fade-up p-4 sm:p-6 bg-accent/10 border-l-4 border-accent" style={{ animationDelay: "275ms" }}>
                    <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-2">
                      Organizing Activity
                    </h4>
                    <p className="text-sm text-foreground leading-relaxed">
                      {briefing.organizing}
                    </p>
                  </div>
                  <Separator />
                </>
              )}

              {/* Public Reception */}
              {briefing.reception && (
                <>
                  <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "350ms" }}>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">
                      Public Reception
                    </h4>
                    <p className="text-sm text-foreground leading-relaxed">
                      {briefing.reception}
                    </p>
                  </div>
                  <Separator />
                </>
              )}

              {/* Timeline */}
              {briefing.timeline.length > 0 && (
                <>
                  <div className="p-4 sm:p-6">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Timeline
                    </h4>
                    <div className="space-y-2">
                      {briefing.timeline.map((event, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
                          <span className="text-sm text-foreground font-medium">
                            {event.event}
                          </span>
                          <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                            {formatDate(event.date)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* News */}
              {briefing.news.length > 0 && (
                <>
                  <div className="p-4 sm:p-6">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Related News
                    </h4>
                    <div className="space-y-3">
                      {briefing.news.map((article, i) => (
                        <a
                          key={i}
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block group"
                        >
                          <p className="text-sm text-foreground group-hover:text-primary transition-colors">
                            {article.title}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            {article.source && (
                              <span className="text-xs text-muted-foreground">
                                {article.source}
                              </span>
                            )}
                            {article.date && (
                              <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                                {formatDate(article.date)}
                              </span>
                            )}
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Similar Bills */}
              {briefing.similar_bills.length > 0 && (
                <>
                  <div className="p-4 sm:p-6">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Same Fight, Other Cities
                    </h4>
                    <div className="space-y-2">
                      {briefing.similar_bills.map((b) => (
                        <Button
                          key={b.id}
                          variant="outline"
                          onClick={() => navigateTo(b.id)}
                          className="w-full text-left h-auto p-3 justify-start items-start flex-col hover:border-primary transition-colors cursor-pointer whitespace-normal"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium text-muted-foreground">
                              {b.city_name}, {b.state}
                            </span>
                            {b.file_number && (
                              <span className="text-xs text-muted-foreground font-[var(--font-mono)]">
                                {b.file_number}
                              </span>
                            )}
                            {b.status && (
                              <Badge className={getStatusClasses(b.status)}>
                                {b.status}
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-foreground line-clamp-2">
                            {b.title}
                          </p>
                        </Button>
                      ))}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Collection Notes */}
              {briefing.collection_notes.length > 0 && (
                <div className="p-4 sm:p-6 bg-muted border-l-4 border-primary">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                    Organizer Notes
                  </h4>
                  <div className="space-y-2">
                    {briefing.collection_notes.map((note, i) => (
                      <div key={i}>
                        <span className="text-xs font-medium text-primary">
                          {note.collection_name}:
                        </span>
                        <p className="text-sm text-foreground leading-relaxed mt-0.5">
                          {note.note}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default BriefingPanel;
