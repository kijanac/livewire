import { useStories } from "../hooks/useStories";
import { useCities } from "../hooks/useCities";
import { useTopics } from "../hooks/useTopics";
import type { Story } from "../types";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatTopic, formatDate } from "@/lib/bill-utils";
import { cn } from "@/lib/utils";
import { ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";

const CATEGORY_LABELS: Record<string, { label: string; classes: string }> = {
  power_shift: { label: "Power Shift", classes: "bg-purple-50 text-purple-900 border border-purple-200" },
  money_move: { label: "Money Move", classes: "bg-emerald-50 text-emerald-900 border border-emerald-200" },
  movement_activity: { label: "Movement", classes: "bg-blue-50 text-blue-900 border border-blue-200" },
  institutional: { label: "Institutional", classes: "bg-amber-50 text-amber-900 border border-amber-200" },
  crisis: { label: "Crisis", classes: "bg-red-50 text-red-900 border border-red-200" },
  other: { label: "Other", classes: "bg-muted text-muted-foreground" },
};

function CategoryBadge({ category }: { category: string | null }) {
  if (!category) return null;
  const config = CATEGORY_LABELS[category];
  if (!config) return null;
  return (
    <span className={cn("inline-flex items-center rounded-4xl px-2 py-0.5 text-xs font-medium", config.classes)}>
      {config.label}
    </span>
  );
}

function StoryCard({ story, index }: { story: Story; index: number }) {
  return (
    <div className="animate-fade-up" style={{ animationDelay: `${index * 60}ms` }}>
      <Card className="overflow-hidden py-0 gap-0">
        <CardHeader className="p-4 pb-3">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-xs font-semibold uppercase tracking-wide text-primary">
              {story.city_name}, {story.state}
            </span>
            <CategoryBadge category={story.category} />
            {story.topics.map((t) => (
              <Badge key={t} variant="secondary" className="text-[10px]">
                {formatTopic(t)}
              </Badge>
            ))}
          </div>

          <a
            href={story.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="group"
          >
            <h3 className="text-sm font-semibold text-foreground leading-snug group-hover:text-primary transition-colors">
              {story.title}
              <ExternalLink className="inline-block ml-1.5 h-3 w-3 opacity-0 group-hover:opacity-50 transition-opacity" />
            </h3>
          </a>

          <div className="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
            {story.source_name && <span>{story.source_name}</span>}
            {story.source_name && story.published_at && <span>&middot;</span>}
            {story.published_at && <span>{formatDate(story.published_at)}</span>}
          </div>
        </CardHeader>

        {story.analysis && (
          <CardContent className="px-4 pb-4 pt-0">
            <p className="text-sm text-foreground/80 leading-relaxed">
              {story.analysis}
            </p>
          </CardContent>
        )}

        {!story.analysis && story.description && (
          <CardContent className="px-4 pb-4 pt-0">
            <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">
              {story.description}
            </p>
          </CardContent>
        )}
      </Card>
    </div>
  );
}

function StoriesView() {
  const { stories, total, page, perPage, filters, loading, setPage, setFilters } = useStories();
  const cities = useCities();
  const topics = useTopics();

  const totalPages = Math.ceil(total / perPage);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-page-heading uppercase tracking-tight text-foreground">Intel</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Political developments across your cities, filtered for organizers
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <Select
          key={filters.city ? "city-set" : "city-empty"}
          value={filters.city || undefined}
          onValueChange={(val) =>
            setFilters({ ...filters, city: !val || val === "__clear__" ? "" : val })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All Cities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__clear__">All Cities</SelectItem>
            {cities.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          key={filters.category ? "cat-set" : "cat-empty"}
          value={filters.category || undefined}
          onValueChange={(val) =>
            setFilters({ ...filters, category: !val || val === "__clear__" ? "" : val })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__clear__">All Categories</SelectItem>
            {Object.entries(CATEGORY_LABELS).map(([key, { label }]) => (
              <SelectItem key={key} value={key}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          key={filters.topic ? "topic-set" : "topic-empty"}
          value={filters.topic || undefined}
          onValueChange={(val) =>
            setFilters({ ...filters, topic: !val || val === "__clear__" ? "" : val })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All Topics" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__clear__">All Topics</SelectItem>
            {topics.map((t) => (
              <SelectItem key={t} value={t}>
                {formatTopic(t)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {!loading && (
          <span className="text-sm font-[var(--font-mono)] text-muted-foreground">
            {total} stor{total !== 1 ? "ies" : "y"}
          </span>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <svg
            className="animate-spin motion-reduce:animate-none h-6 w-6 text-primary"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm text-muted-foreground">Loading stories...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && stories.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">
              No stories yet
              {filters.city || filters.category || filters.topic ? " matching your filters" : ""}.
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Stories are ingested from local news RSS feeds on a recurring schedule.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Stories grid */}
      {!loading && stories.length > 0 && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {stories.map((story, i) => (
              <StoryCard key={story.id} story={story} index={i} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </Button>
              <span className="text-sm font-[var(--font-mono)] text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </>
      )}
    </main>
  );
}

export default StoriesView;
