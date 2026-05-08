<script lang="ts">
  import StatsCards from "./components/StatsCards.svelte";
  import UpcomingActions from "./components/UpcomingActions.svelte";
  import CollectionsSidebar from "./components/CollectionsSidebar.svelte";
  import Filters from "./components/Filters.svelte";
  import BillTable from "./components/BillTable.svelte";
  import { createBills } from "@/hooks/use-bills.svelte";
  import { createStats } from "@/hooks/use-stats.svelte";
  import { createCities } from "@/hooks/use-cities.svelte";
  import { createTopics } from "@/hooks/use-topics.svelte";
  import { createUpcoming } from "@/hooks/use-upcoming.svelte";

  let { refreshKey = 0 }: { refreshKey?: number } = $props();

  const keyRef = () => refreshKey;
  const billsStore = createBills(keyRef);
  const statsStore = createStats(keyRef);
  const { cities } = createCities();
  const { topics } = createTopics();
  const upcomingStore = createUpcoming(keyRef);
</script>

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
  <StatsCards stats={statsStore.stats} loading={statsStore.loading} />
  <UpcomingActions bills={upcomingStore.bills} loading={upcomingStore.loading} />
  <CollectionsSidebar />
  <Filters
    filters={billsStore.filters}
    cities={cities}
    topics={topics}
    onChange={(f) => billsStore.setFilters(f)}
  />

  {#if billsStore.error}
    <div class="mb-4 rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
      {billsStore.error}
    </div>
  {/if}

  <BillTable
    bills={billsStore.bills}
    total={billsStore.total}
    page={billsStore.page}
    perPage={billsStore.perPage}
    onPageChange={(p: number) => (billsStore.page = p)}
    loading={billsStore.loading}
  />
</main>
