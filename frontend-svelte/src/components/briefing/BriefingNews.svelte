<script lang="ts">
  import { Separator } from "@/components/ui/separator";
  import { formatDate } from "@/lib/bill-utils";
  import type { NewsArticle } from "@/types";

  let { news }: { news: NewsArticle[] } = $props();
</script>

{#if news.length > 0}
  <div class="p-4 sm:p-6">
    <h4 class="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Related News</h4>
    <div class="space-y-3">
      {#each news as article}
        <a href={article.url} target="_blank" rel="noopener noreferrer" class="block group">
          <p class="text-sm text-foreground group-hover:text-primary transition-colors">{article.title}</p>
          <div class="flex items-center gap-2 mt-0.5">
            {#if article.source}<span class="text-xs text-muted-foreground">{article.source}</span>{/if}
            {#if article.date}<span class="text-xs font-[var(--font-mono)] text-muted-foreground">{formatDate(article.date)}</span>{/if}
          </div>
        </a>
      {/each}
    </div>
  </div>
  <Separator />
{/if}
