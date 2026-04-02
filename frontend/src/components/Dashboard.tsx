import StatsCards from "./StatsCards";
import UpcomingActions from "./UpcomingActions";
import CollectionsSidebar from "./CollectionsSidebar";
import Filters from "./Filters";
import BillTable from "./BillTable";
import { useBills } from "../hooks/useBills";
import { useStats } from "../hooks/useStats";
import { useCities } from "../hooks/useCities";
import { useTopics } from "../hooks/useTopics";
import { useUpcoming } from "../hooks/useUpcoming";

interface DashboardProps {
  refreshKey: number;
}

function Dashboard({ refreshKey }: DashboardProps) {
  const { bills, total, page, perPage, filters, loading: loadingBills, error, setPage, setFilters } = useBills(refreshKey);
  const { stats, loading: loadingStats } = useStats(refreshKey);
  const cities = useCities();
  const topics = useTopics();
  const { bills: upcomingBills, loading: loadingUpcoming } = useUpcoming(refreshKey);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <StatsCards stats={stats} loading={loadingStats} />
      <UpcomingActions bills={upcomingBills} loading={loadingUpcoming} />
      <CollectionsSidebar />
      <Filters
        filters={filters}
        cities={cities}
        topics={topics}
        onChange={setFilters}
      />

      {error && (
        <div className="mb-4 rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <BillTable
        bills={bills}
        total={total}
        page={page}
        perPage={perPage}
        onPageChange={setPage}
        loading={loadingBills}
      />
    </main>
  );
}

export default Dashboard;
