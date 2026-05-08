export const MOMENTUM_CONFIG = {
  advancing: { label: "Advancing", color: "bg-green-500", textColor: "text-green-600 dark:text-green-400" },
  stalled: { label: "Stalled", color: "bg-red-500", textColor: "text-red-600 dark:text-red-400" },
  stable: { label: "Stable", color: "bg-amber-400", textColor: "text-amber-600 dark:text-amber-400" },
  mixed: { label: "Mixed", color: "bg-muted-foreground/40", textColor: "text-muted-foreground" },
} as const;

export const VOTE_COLORS: Record<"yea" | "nay" | "other", string> = {
  yea: "bg-emerald-500",
  nay: "bg-red-500",
  other: "bg-muted-foreground/30",
};

export const CATEGORY_LABELS: Record<string, { label: string; classes: string }> = {
  power_shift: { label: "Power Shift", classes: "bg-purple-50 text-purple-900 border border-purple-200" },
  money_move: { label: "Money Move", classes: "bg-emerald-50 text-emerald-900 border border-emerald-200" },
  movement_activity: { label: "Movement", classes: "bg-blue-50 text-blue-900 border border-blue-200" },
  institutional: { label: "Institutional", classes: "bg-amber-50 text-amber-900 border border-amber-200" },
  crisis: { label: "Crisis", classes: "bg-red-50 text-red-900 border border-red-200" },
  other: { label: "Other", classes: "bg-muted text-muted-foreground" },
};

export const OUTCOME_INDICATORS = [
  { key: "passed", color: "bg-green-500", label: "passed" },
  { key: "failed", color: "bg-red-500", label: "failed" },
  { key: "pending", color: "bg-amber-400", label: "pending" },
] as const;

export const STAGGER_MS = 75;
export const ROW_STAGGER_MS = 30;
export const CLUSTER_STAGGER_MS = 100;
export const CITY_STAGGER_MS = 80;
export const STORY_STAGGER_MS = 60;

export const staggerDelay = (i: number, step: number = STAGGER_MS) => ({
  animationDelay: `${i * step}ms`,
});
