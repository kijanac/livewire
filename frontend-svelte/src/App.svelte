<script lang="ts">
  import { Button } from "@/components/ui/button";
  import Spinner from "./components/Spinner.svelte";
  import { triggerIngest } from "@/api";
  import { getCollectionName } from "@/hooks/use-collection-stubs.svelte";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";

  type Route =
    | { page: "dashboard" }
    | { page: "collection"; slug: string }
    | { page: "radar" }
    | { page: "allies" }
    | { page: "intel" };

  function parseHash(hash: string): Route {
    const collectionMatch = hash.match(/^#\/collection\/(.+)$/);
    if (collectionMatch) return { page: "collection", slug: collectionMatch[1] };
    if (hash === "#/dashboard") return { page: "dashboard" };
    if (hash === "#/allies") return { page: "allies" };
    if (hash === "#/intel") return { page: "intel" };
    return { page: "radar" };
  }

  let route = $state<Route>(parseHash(window.location.hash));

  $effect(() => {
    const onHashChange = () => {
      route = parseHash(window.location.hash);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  });

  let collectionName = $derived(
    route.page === "collection" ? getCollectionName(route.slug) : null
  );

  let syncing = $state(false);
  let syncResult = $state<string | null>(null);
  let refreshKey = $state(0);

  async function handleSync() {
    syncing = true;
    syncResult = null;
    try {
      const result = await triggerIngest();
      syncResult = `+${result.bills_added} new bills, ${result.bills_updated} updated`;
      refreshKey++;
    } catch {
      syncResult = "Refresh failed. Try again.";
    } finally {
      syncing = false;
      setTimeout(() => (syncResult = null), 5000);
    }
  }

  function navClass(page: string): string {
    const active = route.page === page;
    return `px-3 py-1 text-sm font-semibold uppercase tracking-wide transition-colors ${
      active
        ? "text-primary border-b-2 border-primary -mb-px"
        : "text-muted-foreground hover:text-foreground"
    }`;
  }

  // Lazily load view components
  let viewModule = $derived(
    route.page === "radar"
      ? import("./RadarView.svelte")
      : route.page === "allies"
        ? import("./CoalitionView.svelte")
        : route.page === "intel"
          ? import("./StoriesView.svelte")
          : route.page === "collection"
            ? import("./CollectionView.svelte")
            : import("./Dashboard.svelte")
  );
</script>

<div class="min-h-screen bg-background">
  <header class="sticky top-0 z-10 border-b-2 border-primary bg-card">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-14">
        <div class="flex items-center gap-6">
          <a href="#" class="flex items-center gap-2.5 group">
            <div class="w-7 h-7 bg-primary flex items-center justify-center" aria-hidden="true">
              <svg class="w-4 h-4 text-primary-foreground" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <path d="M3 8h10M8 3l5 5-5 5" />
              </svg>
            </div>
            <span
              class="text-xl font-black tracking-tight uppercase text-foreground font-[var(--font-heading)]"
              style="font-variation-settings: 'opsz' 72, 'WONK' 1"
            >
              Livewire
            </span>
          </a>

          <nav class="flex items-center gap-0.5 border-l-2 border-border pl-4">
            <a href="#" class={navClass("radar")}>Radar</a>
            <a href="#/allies" class={navClass("allies")}>Allies</a>
            <a href="#/intel" class={navClass("intel")}>Intel</a>
            <a href="#/dashboard" class={navClass("dashboard")}>Dashboard</a>
          </nav>

          {#if route.page === "collection"}
            <span class="text-sm text-muted-foreground font-semibold uppercase tracking-wide">
              / {collectionName || "Collection"}
            </span>
          {/if}
        </div>

        <div class="flex items-center gap-3 flex-shrink-0">
          {#if syncResult}
            <span class="hidden sm:inline text-xs font-[var(--font-mono)] text-muted-foreground">
              {syncResult}
            </span>
          {/if}
          {#if route.page === "dashboard"}
            <Button
              onclick={handleSync}
              disabled={syncing}
              variant="outline"
              size="icon-sm"
              class="sm:size-auto sm:h-7 sm:px-2.5 font-[var(--font-mono)] text-xs uppercase tracking-wider"
            >
              {#if syncing}
                <Spinner size={14} />
              {:else}
                <RefreshCw class="h-3.5 w-3.5" />
              {/if}
              <span class="hidden sm:inline">
                {syncing ? "Refreshing" : "Refresh Data"}
              </span>
            </Button>
          {/if}
        </div>
      </div>
    </div>
  </header>

  {#await viewModule then mod}
    <mod.default refreshKey={refreshKey} slug={route.page === "collection" ? route.slug : undefined} />
  {:catch err}
    <div class="flex items-center justify-center py-24">
      <p class="text-destructive">Failed to load page: {err.message}</p>
    </div>
  {/await}
</div>
