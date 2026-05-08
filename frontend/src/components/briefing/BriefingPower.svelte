<script lang="ts">
  import { Badge } from "@/components/ui/badge";
  import { Separator } from "@/components/ui/separator";
  import { VOTE_COLORS } from "@/lib/visual-tokens";
  import { formatDate } from "@/lib/bill-utils";
  import type { PowerSection } from "@/types";

  function colorKey(vote: string): keyof typeof VOTE_COLORS {
    return vote === "yea" ? "yea" : vote === "nay" ? "nay" : "other";
  }

  let { power }: { power: PowerSection | null } = $props();
</script>

{#if power && (power.sponsors.length > 0 || power.votes || power.actions.length > 0)}
  {@const v = power.votes}
  {@const totalVotes = v ? v.yea + v.nay + v.abstain + v.absent + v.other : 0}

  <div class="animate-fade-up p-4 sm:p-6" style="animation-delay: 200ms">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Power Map</h4>

    {#if power.sponsors.length > 0}
      <div class="mb-4">
        <span class="text-xs font-medium text-muted-foreground">Sponsors</span>
        <div class="flex flex-wrap gap-1.5 mt-1.5">
          {#each power.sponsors as s (s.id)}
            <span class="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-primary/10 text-primary font-medium">
              {s.name}
              {#if s.district}<span class="text-primary/60">D{s.district}</span>{/if}
            </span>
          {/each}
        </div>
      </div>
    {/if}

    {#if v && totalVotes > 0}
      <div class="mb-4">
        <span class="text-xs font-medium text-muted-foreground">Vote Breakdown</span>
        <div class="mt-1.5">
          <div class="flex h-3 rounded-full overflow-hidden bg-muted">
            {#if v.yea > 0}<div class={VOTE_COLORS.yea} style="width: {(v.yea / totalVotes) * 100}%" title="Yea: {v.yea}" />{/if}
            {#if v.nay > 0}<div class={VOTE_COLORS.nay} style="width: {(v.nay / totalVotes) * 100}%" title="Nay: {v.nay}" />{/if}
            {#if v.abstain + v.absent + v.other > 0}<div class={VOTE_COLORS.other} style="width: {((v.abstain + v.absent + v.other) / totalVotes) * 100}%" title="Other: {v.abstain + v.absent + v.other}" />{/if}
          </div>
          <div class="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
            {#if v.yea > 0}<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full {VOTE_COLORS.yea}" /> Yea {v.yea}</span>{/if}
            {#if v.nay > 0}<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full {VOTE_COLORS.nay}" /> Nay {v.nay}</span>{/if}
            {#if v.abstain > 0}<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full {VOTE_COLORS.other}" /> Abstain {v.abstain}</span>{/if}
            {#if v.absent > 0}<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full {VOTE_COLORS.other}" /> Absent {v.absent}</span>{/if}
          </div>
          {#if v.records.length > 0}
            <details class="mt-2">
              <summary class="text-xs text-primary cursor-pointer hover:text-primary/80">Show individual votes ({v.records.length})</summary>
              <div class="mt-1.5 grid grid-cols-2 gap-1">
                {#each v.records as r}
                  <div class="flex items-center gap-1.5 text-xs">
                    <span class="w-1.5 h-1.5 rounded-full flex-shrink-0 {VOTE_COLORS[colorKey(r.vote)]}" />
                    <span class="text-foreground truncate">{r.official}</span>
                  </div>
                {/each}
              </div>
            </details>
          {/if}
        </div>
      </div>
    {/if}

    {#if power.actions.length > 0}
      <div class="mb-4">
        <span class="text-xs font-medium text-muted-foreground">Action History</span>
        <div class="mt-1.5 space-y-1.5">
          {#each power.actions.slice(-8) as a}
            <div class="flex items-start gap-2">
              <div class="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 mt-1.5 flex-shrink-0" />
              <div class="min-w-0">
                <span class="text-xs text-foreground">{a.action || "Action"}</span>
                <div class="flex items-center gap-2">
                  {#if a.date}<span class="text-xs font-[var(--font-mono)] text-muted-foreground">{formatDate(a.date)}</span>{/if}
                  {#if a.body}<span class="text-xs text-muted-foreground">{a.body}</span>{/if}
                  {#if a.result}<Badge variant="secondary" class="text-[10px] px-1 py-0">{a.result}</Badge>{/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if power.voting_patterns && power.voting_patterns.patterns.length > 0}
      <div class="mb-4">
        <span class="text-xs font-medium text-muted-foreground">
          Voting History on Similar Bills
          <span class="font-[var(--font-mono)] ml-1">({power.voting_patterns.similar_bill_count} bills)</span>
        </span>
        <div class="mt-1.5 space-y-2">
          {#each power.voting_patterns.patterns as p (p.official_id)}
            <div class="flex items-center gap-2">
              <div class="w-24 truncate text-xs text-foreground font-medium flex items-center gap-1">
                {p.name}
                {#if p.is_swing}<span class="text-[10px] font-bold text-primary" title="Swing voter (30-70% alignment)">SWING</span>{/if}
              </div>
              <div class="flex-1 flex items-center gap-2">
                <div class="flex-1 h-2 rounded-full overflow-hidden bg-muted">
                  <div class={p.is_swing ? "bg-amber-400 h-full" : p.alignment_pct >= 50 ? "bg-emerald-500 h-full" : "bg-red-500 h-full"} style="width: {p.alignment_pct}%" />
                </div>
                <span class="text-xs font-[var(--font-mono)] text-muted-foreground w-16 text-right">{p.yea}/{p.total} yea</span>
              </div>
            </div>
          {/each}
        </div>
        {#if power.voting_patterns.swing_voters.length > 0}
          <p class="text-xs text-primary font-medium mt-2">
            Swing vote{power.voting_patterns.swing_voters.length > 1 ? "s" : ""}: {power.voting_patterns.swing_voters.join(", ")}
          </p>
        {/if}
      </div>
    {/if}

    {#if power.analysis}
      <div class="mt-3 p-3 rounded-md bg-primary/5 border border-primary/10">
        <p class="text-sm text-foreground leading-relaxed">{power.analysis}</p>
      </div>
    {/if}
  </div>
  <Separator />
{/if}
