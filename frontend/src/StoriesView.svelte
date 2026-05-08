<script lang="ts">
  import { createStories } from "@/hooks/use-stories.svelte";
  import { createCities } from "@/hooks/use-cities.svelte";
  import { createTopics } from "@/hooks/use-topics.svelte";
  import { useErrorToast } from "@/hooks/use-error-toast.svelte";
  import type { Story } from "@/types";
  import { Card, CardHeader, CardContent } from "@/components/ui/card";
  import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
  } from "@/components/ui/select";
  import { Badge } from "@/components/ui/badge";
  import { Button } from "@/components/ui/button";
  import Spinner from "./components/Spinner.svelte";
  import { formatTopic, formatDate } from "@/lib/bill-utils";
  import { cn } from "@/lib/utils";
  import { CATEGORY_LABELS, STORY_STAGGER_MS } from "@/lib/visual-tokens";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";

  const storiesStore = createStories();
  const citiesStore = createCities();
  const topicsStore = createTopics();
  useErrorToast(storiesStore.error, "Failed to load stories");

  const CLEAR = "__clear__";
  let totalPages = $derived(Math.ceil(storiesStore.total / storiesStore.perPage));

  function pluralize(n: number, singular: string, plural: string) {
    return n === 1 ? `${n} ${singular}` : `${n} ${plural}`;
  }
</script>

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
  <div class="mb-6">
    <h2 class="text-page-heading uppercase tracking-tight text-foreground">Intel</h2>
    <p class="text-sm text-muted-foreground mt-1">Political developments across your cities, filtered for organizers</p>
  </div>

  <!-- Filters -->
  <div class="flex items-center gap-3 mb-6 flex-wrap">
    <Select
      value={storiesStore.filters.city || undefined}
      onValueChange={(val) =>
        storiesStore.setFilters({ ...storiesStore.filters, city: (!val || val === CLEAR) ? "" : (val ?? "") })
      }
    >
      <SelectTrigger>{storiesStore.filters.city ? (cities.find(c => c.id === storiesStore.filters.city)?.name ?? storiesStore.filters.city) : "All Cities"}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR}>All Cities</SelectItem>
        {#each citiesStore.cities as c (c.id)}
          <SelectItem value={c.id}>{c.name}</SelectItem>
        {/each}
      </SelectContent>
    </Select>

    <Select
      value={storiesStore.filters.category || undefined}
      onValueChange={(val) =>
        storiesStore.setFilters({ ...storiesStore.filters, category: (!val || val === CLEAR) ? "" : (val ?? "") })
      }
    >
      <SelectTrigger>{storiesStore.filters.category ? (CATEGORY_LABELS[storiesStore.filters.category]?.label ?? storiesStore.filters.category) : "All Categories"}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR}>All Categories</SelectItem>
        {#each Object.entries(CATEGORY_LABELS) as [key, { label }]}
          <SelectItem value={key}>{label}</SelectItem>
        {/each}
      </SelectContent>
    </Select>

    <Select
      value={storiesStore.filters.topic || undefined}
      onValueChange={(val) =>
        storiesStore.setFilters({ ...storiesStore.filters, topic: (!val || val === CLEAR) ? "" : (val ?? "") })
      }
    >
      <SelectTrigger>{storiesStore.filters.topic ? formatTopic(storiesStore.filters.topic) : "All Topics"}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR}>All Topics</SelectItem>
        {#each topicsStore.topics as t (t)}
          <SelectItem value={t}>{formatTopic(t)}</SelectItem>
        {/each}
      </SelectContent>
    </Select>

    {#if !storiesStore.loading}
      <span class="text-sm font-[var(--font-mono)] text-muted-foreground">
        {pluralize(storiesStore.total, "story", "stories")}
      </span>
    {/if}
  </div>

  {#if storiesStore.loading}
    <div class="flex flex-col items-center justify-center py-16 gap-3">
      <Spinner size={24} class="text-primary" />
      <span class="text-sm text-muted-foreground">Loading stories...</span>
    </div>
  {:else if storiesStore.stories.length === 0}
    <Card>
      <CardContent class="p-12 text-center">
        <p class="text-muted-foreground">
          No stories yet{storiesStore.filters.city || storiesStore.filters.category || storiesStore.filters.topic ? " matching your filters" : ""}.
        </p>
        <p class="text-sm text-muted-foreground mt-1">Stories are ingested from local news RSS feeds on a recurring schedule.</p>
      </CardContent>
    </Card>
  {:else}
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {#each storiesStore.stories as story, i (story.id)}
        <div class="animate-fade-up" style="animation-delay: {i * STORY_STAGGER_MS}ms">
          <Card class="overflow-hidden py-0 gap-0">
            <CardHeader class="p-4 pb-3">
              <div class="flex items-center gap-2 mb-2 flex-wrap">
                <span class="text-xs font-semibold uppercase tracking-wide text-primary">
                  {story.city_name}, {story.state}
                </span>
                {#if story.category}
                  {@const cat = CATEGORY_LABELS[story.category]}
                  {#if cat}
                    <span class={cn("inline-flex items-center rounded-4xl px-2 py-0.5 text-xs font-medium", cat.classes)}>
                      {cat.label}
                    </span>
                  {/if}
                {/if}
                {#each story.topics as t}
                  <Badge variant="secondary" class="text-[10px]">{formatTopic(t)}</Badge>
                {/each}
              </div>

              <a href={story.source_url} target="_blank" rel="noopener noreferrer" class="group">
                <h3 class="text-sm font-semibold text-foreground leading-snug group-hover:text-primary transition-colors">
                  {story.title}
                  <ExternalLink class="inline-block ml-1.5 h-3 w-3 opacity-0 group-hover:opacity-50 transition-opacity" />
                </h3>
              </a>

              <div class="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
                {#if story.source_name}<span>{story.source_name}</span>{/if}
                {#if story.source_name && story.published_at}<span>&middot;</span>{/if}
                {#if story.published_at}<span>{formatDate(story.published_at)}</span>{/if}
              </div>
            </CardHeader>

            {#if story.analysis}
              <CardContent class="px-4 pb-4 pt-0">
                <p class="text-sm text-foreground/80 leading-relaxed">{story.analysis}</p>
              </CardContent>
            {:else if story.description}
              <CardContent class="px-4 pb-4 pt-0">
                <p class="text-sm text-muted-foreground leading-relaxed line-clamp-3">{story.description}</p>
              </CardContent>
            {/if}
          </Card>
        </div>
      {/each}
    </div>

    {#if totalPages > 1}
      <div class="flex items-center justify-between mt-6">
        <Button variant="outline" size="sm" disabled={storiesStore.page <= 1} onclick={() => (storiesStore.page--)}>
          <ChevronLeft class="h-3.5 w-3.5" /> Previous
        </Button>
        <span class="text-sm font-[var(--font-mono)] text-muted-foreground">
          Page {storiesStore.page} of {totalPages}
        </span>
        <Button variant="outline" size="sm" disabled={storiesStore.page >= totalPages} onclick={() => (storiesStore.page++)}>
          Next <ChevronRight class="h-3.5 w-3.5" />
        </Button>
      </div>
    {/if}
  {/if}
</main>
