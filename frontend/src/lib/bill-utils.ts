/**
 * Shared utility functions for bill display, used across multiple components.
 */

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatShortDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(date);
}

export function formatTopic(topic: string): string {
  return topic
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const now = new Date();
  const date = new Date(dateStr);
  return Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export type StatusVariant = "success" | "warning" | "destructive" | "default";

export function getStatusVariant(status: string | null): StatusVariant {
  if (!status) return "default";
  const s = status.toLowerCase();

  if (
    s.includes("passed") ||
    s.includes("adopted") ||
    s.includes("approved") ||
    s.includes("enacted") ||
    s.includes("signed")
  )
    return "success";

  if (
    s.includes("committee") ||
    s.includes("pending") ||
    s.includes("hearing") ||
    s.includes("introduced") ||
    s.includes("referred") ||
    s.includes("filed")
  )
    return "warning";

  if (
    s.includes("failed") ||
    s.includes("withdrawn") ||
    s.includes("vetoed") ||
    s.includes("rejected")
  )
    return "destructive";

  return "default";
}

/** Map status variant to Tailwind classes for badge styling.
 *  These use semantic green/amber/red intentionally — they communicate
 *  status meaning independent of the brand palette. */
export function getStatusClasses(status: string | null): string {
  const variant = getStatusVariant(status);
  switch (variant) {
    case "success":
      return "bg-green-50 text-green-900 border border-green-200";
    case "warning":
      return "bg-amber-50 text-amber-900 border border-amber-200";
    case "destructive":
      return "bg-red-50 text-red-900 border border-red-200";
    default:
      return "bg-muted text-muted-foreground";
  }
}
