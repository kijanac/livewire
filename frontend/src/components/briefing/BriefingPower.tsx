import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { VOTE_COLORS } from "@/lib/visual-tokens";
import { formatDate } from "@/lib/bill-utils";
import type { PowerSection } from "@/types";

interface BriefingPowerProps {
  power: PowerSection | null;
}

export function BriefingPower({ power }: BriefingPowerProps) {
  if (!power) return null;
  if (power.sponsors.length === 0 && !power.votes && power.actions.length === 0) return null;

  const v = power.votes;
  const totalVotes = v ? v.yea + v.nay + v.abstain + v.absent + v.other : 0;

  return (
    <>
      <div className="animate-fade-up p-4 sm:p-6" style={{ animationDelay: "200ms" }}>
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Power Map
        </h4>

        {power.sponsors.length > 0 && (
          <div className="mb-4">
            <span className="text-xs font-medium text-muted-foreground">Sponsors</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {power.sponsors.map((s) => (
                <span
                  key={s.id}
                  className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-primary/10 text-primary font-medium"
                >
                  {s.name}
                  {s.district && <span className="text-primary/60">D{s.district}</span>}
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
                    className={VOTE_COLORS.yea}
                    style={{ width: `${(v.yea / totalVotes) * 100}%` }}
                    title={`Yea: ${v.yea}`}
                  />
                )}
                {v.nay > 0 && (
                  <div
                    className={VOTE_COLORS.nay}
                    style={{ width: `${(v.nay / totalVotes) * 100}%` }}
                    title={`Nay: ${v.nay}`}
                  />
                )}
                {v.abstain + v.absent + v.other > 0 && (
                  <div
                    className={VOTE_COLORS.other}
                    style={{ width: `${((v.abstain + v.absent + v.other) / totalVotes) * 100}%` }}
                    title={`Other: ${v.abstain + v.absent + v.other}`}
                  />
                )}
              </div>
              <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                {v.yea > 0 && (
                  <span className="flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${VOTE_COLORS.yea}`} />
                    Yea {v.yea}
                  </span>
                )}
                {v.nay > 0 && (
                  <span className="flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${VOTE_COLORS.nay}`} />
                    Nay {v.nay}
                  </span>
                )}
                {v.abstain > 0 && (
                  <span className="flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${VOTE_COLORS.other}`} />
                    Abstain {v.abstain}
                  </span>
                )}
                {v.absent > 0 && (
                  <span className="flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${VOTE_COLORS.other}`} />
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
                    {v.records.map((r, i) => {
                      const colorKey = r.vote === "yea" ? "yea" : r.vote === "nay" ? "nay" : "other";
                      return (
                        <div key={i} className="flex items-center gap-1.5 text-xs">
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${VOTE_COLORS[colorKey]}`} />
                          <span className="text-foreground truncate">{r.official}</span>
                        </div>
                      );
                    })}
                  </div>
                </details>
              )}
            </div>
          </div>
        )}

        {power.actions.length > 0 && (
          <div className="mb-4">
            <span className="text-xs font-medium text-muted-foreground">Action History</span>
            <div className="mt-1.5 space-y-1.5">
              {power.actions.slice(-8).map((a, i) => (
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
                      {a.body && <span className="text-xs text-muted-foreground">{a.body}</span>}
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

        {power.voting_patterns && power.voting_patterns.patterns.length > 0 && (
          <div className="mb-4">
            <span className="text-xs font-medium text-muted-foreground">
              Voting History on Similar Bills
              <span className="font-[var(--font-mono)] ml-1">
                ({power.voting_patterns.similar_bill_count} bills)
              </span>
            </span>
            <div className="mt-1.5 space-y-2">
              {power.voting_patterns.patterns.map((p) => (
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
            {power.voting_patterns.swing_voters.length > 0 && (
              <p className="text-xs text-primary font-medium mt-2">
                Swing vote{power.voting_patterns.swing_voters.length > 1 ? "s" : ""}: {power.voting_patterns.swing_voters.join(", ")}
              </p>
            )}
          </div>
        )}

        {power.analysis && (
          <div className="mt-3 p-3 rounded-md bg-primary/5 border border-primary/10">
            <p className="text-sm text-foreground leading-relaxed">{power.analysis}</p>
          </div>
        )}
      </div>
      <Separator />
    </>
  );
}
