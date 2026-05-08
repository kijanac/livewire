<script lang="ts">
  import type { BillFilters, City } from "@/types";
  import { Input } from "@/components/ui/input";
  import { Button } from "@/components/ui/button";
  import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
  } from "@/components/ui/select";
  import { formatTopic } from "@/lib/bill-utils";
  import Search from "@lucide/svelte/icons/search";

  let { filters, cities, topics, onChange }: {
    filters: BillFilters;
    cities: City[];
    topics: string[];
    onChange: (filters: BillFilters) => void;
  } = $props();

  const COMMON_STATUSES = [
    "Adopted", "Approved", "Committee", "Enacted", "Failed", "Filed",
    "Hearing Scheduled", "Introduced", "Passed", "Pending", "Referred",
    "Signed", "Vetoed", "Withdrawn",
  ];

  const COMMON_TYPES = [
    "Ordinance", "Resolution", "Communication", "Report", "Motion",
    "Order", "Petition", "Proclamation", "Executive Order", "Local Law",
  ];

  const CLEAR = "__clear__";

  let showMore = $state(false);

  function update(field: keyof BillFilters, value: string) {
    onChange({ ...filters, [field]: value });
  }

  let moreFiltersActive = $derived(!!(filters.status || filters.type_name || filters.urgency));

  let cityLabel = $derived(filters.city ? (cities.find(c => c.id === filters.city)?.name ?? filters.city) : "Any City");
  let topicLabel = $derived(filters.topic ? formatTopic(filters.topic) : "Any Issue");
  let levelLabel = $derived(filters.jurisdiction_level === "city" ? "City Council" : filters.jurisdiction_level === "state" ? "State Legislature" : "All Levels");
</script>

<div class="mb-6 space-y-2">
  <!-- Primary filters: always visible -->
  <div class="flex flex-wrap gap-2 sm:gap-3">
    <div class="relative flex-1 min-w-[180px]">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" aria-hidden="true" />
      <Input
        type="text"
        value={filters.search}
        oninput={(e) => update("search", e.currentTarget.value)}
        placeholder="Search by keyword..."
        class="w-full pl-9"
      />
    </div>

    <Select
      value={filters.jurisdiction_level || undefined}
      onValueChange={(val) => {
        update("jurisdiction_level", val === CLEAR ? "" : (val ?? ""));
        update("city", "");
      }}
    >
      <SelectTrigger>{levelLabel}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR} label="All Levels">All Levels</SelectItem>
        <SelectItem value="city" label="City Council">City Council</SelectItem>
        <SelectItem value="state" label="State Legislature">State Legislature</SelectItem>
      </SelectContent>
    </Select>

    <Select
      value={filters.city || undefined}
      onValueChange={(val) => update("city", val === CLEAR ? "" : (val ?? ""))}
    >
      <SelectTrigger>{cityLabel}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR} label="Any City">Any City</SelectItem>
        {#each cities as city (city.id)}
          <SelectItem value={city.id} label={`${city.name}, ${city.state}`}>{city.name}, {city.state}</SelectItem>
        {/each}
      </SelectContent>
    </Select>

    <Select
      value={filters.topic || undefined}
      onValueChange={(val) => update("topic", val === CLEAR ? "" : (val ?? ""))}
    >
      <SelectTrigger>{topicLabel}</SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR} label="Any Issue">Any Issue</SelectItem>
        {#each topics as topic (topic)}
          <SelectItem value={topic} label={formatTopic(topic)}>{formatTopic(topic)}</SelectItem>
        {/each}
      </SelectContent>
    </Select>

    <Button
      variant={showMore || moreFiltersActive ? "secondary" : "outline"}
      size="default"
      onclick={() => (showMore = !showMore)}
      class="gap-1"
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75" />
      </svg>
      Filters
      {#if moreFiltersActive}
        <span class="ml-0.5 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold rounded-full bg-primary text-primary-foreground">
          {[filters.status, filters.type_name, filters.urgency].filter(Boolean).length}
        </span>
      {/if}
    </Button>
  </div>

  <!-- Secondary filters: toggleable -->
  {#if showMore}
    <div class="flex flex-wrap gap-2 sm:gap-3 animate-fade-up">
      <Select
        value={filters.status || undefined}
        onValueChange={(val) => update("status", val === CLEAR ? "" : (val ?? ""))}
      >
        <SelectTrigger>{filters.status || "Any Status"}</SelectTrigger>
        <SelectContent>
          <SelectItem value={CLEAR} label="Any Status">Any Status</SelectItem>
          {#each COMMON_STATUSES as status (status)}
            <SelectItem value={status} label={status}>{status}</SelectItem>
          {/each}
        </SelectContent>
      </Select>

      <Select
        value={filters.type_name || undefined}
        onValueChange={(val) => update("type_name", val === CLEAR ? "" : (val ?? ""))}
      >
        <SelectTrigger>{filters.type_name || "Any Type"}</SelectTrigger>
        <SelectContent>
          <SelectItem value={CLEAR} label="Any Type">Any Type</SelectItem>
          {#each COMMON_TYPES as type (type)}
            <SelectItem value={type} label={type}>{type}</SelectItem>
          {/each}
        </SelectContent>
      </Select>

      <Select
        value={filters.urgency || undefined}
        onValueChange={(val) => update("urgency", val === CLEAR ? "" : (val ?? ""))}
      >
        <SelectTrigger>{filters.urgency === "urgent" ? "This Week" : filters.urgency === "soon" ? "This Month" : "Any Timeline"}</SelectTrigger>
        <SelectContent>
          <SelectItem value={CLEAR} label="Any Timeline">Any Timeline</SelectItem>
          <SelectItem value="urgent" label="This Week">This Week</SelectItem>
          <SelectItem value="soon" label="This Month">This Month</SelectItem>
        </SelectContent>
      </Select>
    </div>
  {/if}
</div>
