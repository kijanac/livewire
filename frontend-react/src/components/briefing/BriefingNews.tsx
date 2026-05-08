import { Separator } from "@/components/ui/separator";
import { formatDate } from "@/lib/bill-utils";
import type { NewsArticle } from "@/types";

interface BriefingNewsProps {
  news: NewsArticle[];
}

export function BriefingNews({ news }: BriefingNewsProps) {
  if (news.length === 0) return null;
  return (
    <>
      <div className="p-4 sm:p-6">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Related News
        </h4>
        <div className="space-y-3">
          {news.map((article, i) => (
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
                  <span className="text-xs text-muted-foreground">{article.source}</span>
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
  );
}
