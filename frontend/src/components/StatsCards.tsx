import type { StatsResponse } from "../types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatTopic } from "@/lib/bill-utils";

interface StatsCardsProps {
  stats: StatsResponse | null;
  loading: boolean;
}

function StatsCards({ stats, loading }: StatsCardsProps) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse motion-reduce:animate-none">
            <CardContent>
              <div className="h-4 bg-muted rounded w-20 mb-3" />
              <div className="h-8 bg-muted rounded w-16 mb-2" />
              <div className="h-3 bg-muted rounded w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-6">
      {/* Up for Action This Week */}
      <Card
        className={cn(
          stats.moving_this_week > 0 && "bg-primary text-primary-foreground border-primary"
        )}
      >
        <CardContent>
          <div
            className={cn(
              "text-xs font-medium uppercase tracking-wider mb-1",
              stats.moving_this_week > 0
                ? "text-primary-foreground/80"
                : "text-muted-foreground"
            )}
          >
            Up for Action This Week
          </div>
          <div
            className={cn(
              "text-hero-number",
              stats.moving_this_week > 0
                ? "text-primary-foreground"
                : "text-foreground"
            )}
          >
            {stats.moving_this_week}
          </div>
          <div
            className={cn(
              "text-xs mt-1",
              stats.moving_this_week > 0
                ? "text-primary-foreground/70"
                : "text-muted-foreground"
            )}
          >
            bills with hearings or votes in 7 days
          </div>
        </CardContent>
      </Card>

      {/* Trending Issues */}
      <Card>
        <CardContent>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Trending Issues
          </div>
          {stats.hot_topics.length > 0 ? (
            <div className="flex flex-col gap-1.5">
              {stats.hot_topics.map((t) => (
                <div key={t.topic} className="flex items-center justify-between">
                  <Badge variant="secondary">
                    {formatTopic(t.topic)}
                  </Badge>
                  <span className="text-xs font-[var(--font-mono)] text-muted-foreground">
                    {t.count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">Issue tags loading...</div>
          )}
        </CardContent>
      </Card>

      {/* Hottest City */}
      <Card>
        <CardContent>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            Hottest City
          </div>
          {stats.most_active_city ? (
            <>
              <div className="text-page-heading text-foreground">
                {stats.most_active_city.city_name}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {stats.most_active_city.upcoming_count} hearing{stats.most_active_city.upcoming_count !== 1 ? "s" : ""} this week
              </div>
            </>
          ) : (
            <div className="text-sm text-muted-foreground mt-2">No hearings scheduled</div>
          )}
        </CardContent>
      </Card>

      {/* Just Filed */}
      <Card
        className={cn(
          stats.new_bills_7d > 0 && "bg-accent text-accent-foreground border-accent"
        )}
      >
        <CardContent>
          <div
            className={cn(
              "text-xs font-medium uppercase tracking-wider mb-1",
              stats.new_bills_7d > 0
                ? "text-accent-foreground/80"
                : "text-muted-foreground"
            )}
          >
            Just Filed
          </div>
          <div
            className={cn(
              "text-hero-number",
              stats.new_bills_7d > 0
                ? "text-accent-foreground"
                : "text-foreground"
            )}
          >
            {stats.new_bills_7d}
          </div>
          <div
            className={cn(
              "text-xs mt-1",
              stats.new_bills_7d > 0
                ? "text-accent-foreground/70"
                : "text-muted-foreground"
            )}
          >
            new bills this week
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default StatsCards;
