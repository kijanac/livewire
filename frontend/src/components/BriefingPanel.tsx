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

                    {briefing.power!.voting_patterns && briefing.power!.voting_patterns.patterns.length > 0 && (
                      <div className="mb-4">
                        <span className="text-xs font-medium text-muted-foreground">
                          Voting History on Similar Bills
                          <span className="font-[var(--font-mono)] ml-1">
                            ({briefing.power!.voting_patterns.similar_bill_count} bills)
                          </span>
                        </span>
                        <div className="mt-1.5 space-y-2">
                          {briefing.power!.voting_patterns.patterns.map((p) => (
                            <div key={p.official_id} className="flex items-center gap-2">
                              <div className="w-24 truncate text-xs text-foreground font-medium flex items-center gap-1">
                                {p.name}
                                {p.is_swing && (
                                  <span className="text-[10px] font-bold text-primary" title="Swing voter (30-70% alignment)">
                                    SWING
                                  </span>
                                )}
                              </div>
                              <div className="flex-1 flex items-center gap-2">
                                <div className="flex-1 h-2 rounded-full overflow-hidden bg-muted">
                                  <div
                                    className={p.is_swing ? "bg-amber-400 h-full" : p.alignment_pct >= 50 ? "bg-emerald-500 h-full" : "bg-red-500 h-full"}
                                    style={{ width: `${p.alignment_pct}%` }}
                                  />
                                </div>
                                <span className="text-xs font-[var(--font-mono)] text-muted-foreground w-16 text-right">
                                  {p.yea}/{p.total} yea
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                        {briefing.power!.voting_patterns.swing_voters.length > 0 && (
                          <p className="text-xs text-primary font-medium mt-2">
                            Swing vote{briefing.power!.voting_patterns.swing_voters.length > 1 ? "s" : ""}: {briefing.power!.voting_patterns.swing_voters.join(", ")}
                          </p>
                        )}
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

              {/* Narrative Intelligence */}
              {briefing.narrative && (briefing.narrative.frames.length > 0 || briefing.narrative.talking_points.length > 0) && (
                <>
                  <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "400ms" }}>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Narrative Analysis
                    </h4>

                    {briefing.narrative.frames.length > 0 && (
                      <div className="mb-4">
                        <span className="text-xs font-medium text-muted-foreground">Media Framing</span>
                        <div className="mt-1.5 space-y-1.5">
                          {briefing.narrative.frames.map((f, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <span className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${
                                f.stance === "support" ? "bg-green-500" :
                                f.stance === "opposition" ? "bg-red-500" :
                                "bg-muted-foreground/40"
                              }`} />
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
                      {briefing.narrative.support_narrative && (
                        <div className="p-3 rounded-md bg-green-500/5 border border-green-500/10">
                          <span className="text-xs font-medium text-green-600 dark:text-green-400">Support Frame</span>
                          <p className="text-sm text-foreground leading-relaxed mt-1">
                            {briefing.narrative.support_narrative}
                          </p>
                        </div>
                      )}
                      {briefing.narrative.opposition_narrative && (
                        <div className="p-3 rounded-md bg-red-500/5 border border-red-500/10">
                          <span className="text-xs font-medium text-red-600 dark:text-red-400">Opposition Frame</span>
                          <p className="text-sm text-foreground leading-relaxed mt-1">
                            {briefing.narrative.opposition_narrative}
                          </p>
                        </div>
                      )}
                    </div>

                    {briefing.narrative.narrative_trajectory && (
                      <div className="mt-3 flex items-start gap-2">
                        <svg className="w-3.5 h-3.5 text-muted-foreground mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                          <polyline points="17 6 23 6 23 12" />
                        </svg>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {briefing.narrative.narrative_trajectory}
                        </p>
                      </div>
                    )}

                    {briefing.narrative.talking_points.length > 0 && (
                      <div className="mt-4 p-3 rounded-md bg-primary/5 border border-primary/10">
                        <span className="text-xs font-bold text-primary uppercase tracking-wider">
                          Talking Points
                        </span>
                        <ul className="mt-2 space-y-1.5">
                          {briefing.narrative.talking_points.map((tp, i) => (
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

              {/* Documents */}
              {briefing.documents.length > 0 && (
                <>
                  <div className="p-4 sm:p-6">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Documents
                    </h4>
                    <div className="space-y-2">
                      {briefing.documents.map((doc) => (
                        <a
                          key={doc.id}
                          href={doc.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 group"
                        >
                          <svg className="h-4 w-4 text-muted-foreground group-hover:text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                          </svg>
                          <span className="text-sm text-foreground group-hover:text-primary transition-colors truncate">
                            {doc.name}
                          </span>
                        </a>
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

              {/* Coalition Intelligence */}
              {briefing.coalition && (briefing.coalition.ally_cities.length > 0 || briefing.coalition.contested_cities.length > 0 || briefing.coalition.insight) && (
                <>
                  <div className="animate-fade-up p-4 sm:p-6 bg-accent/5 border-l-4 border-accent" style={{ animationDelay: "450ms" }}>
                    <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-3">
                      Coalition Intel
                    </h4>

                    {briefing.coalition.ally_cities.length > 0 && (
                      <div className="mb-3">
                        <span className="text-xs font-medium text-green-600 dark:text-green-400">Allies (passed similar bills)</span>
                        <div className="flex flex-wrap gap-1.5 mt-1.5">
                          {briefing.coalition.ally_cities.map((city) => (
                            <Badge key={city} variant="secondary" className="bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20">
                              {city}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {briefing.coalition.contested_cities.length > 0 && (
                      <div className="mb-3">
                        <span className="text-xs font-medium text-amber-600 dark:text-amber-400">In play (still deciding)</span>
                        <div className="flex flex-wrap gap-1.5 mt-1.5">
                          {briefing.coalition.contested_cities.map((city) => (
                            <Badge key={city} variant="secondary" className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20">
                              {city}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {briefing.coalition.insight && (
                      <div className="mt-3 p-3 rounded-md bg-accent/10 border border-accent/20">
                        <p className="text-sm text-foreground leading-relaxed">
                          {briefing.coalition.insight}
                        </p>
                      </div>
                    )}
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
