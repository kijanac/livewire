import { useState, useEffect, useCallback } from "react";
import StatsCards from "./StatsCards";
import UpcomingActions from "./UpcomingActions";
import CollectionsSidebar from "./CollectionsSidebar";
import Filters from "./Filters";
import BillTable from "./BillTable";
import {
  fetchBills,
  fetchCities,
  fetchStats,
  fetchTopics,
  fetchUpcoming,
} from "../api";
import type { Bill, City, StatsResponse, BillFilters } from "../types";

interface DashboardProps {
  refreshKey: number;
}

const PER_PAGE = 25;

const INITIAL_FILTERS: BillFilters = {
  city: "",
  status: "",
  type_name: "",
  topic: "",
  urgency: "",
  search: "",
};

function Dashboard({ refreshKey }: DashboardProps) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [cities, setCities] = useState<City[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [upcomingBills, setUpcomingBills] = useState<Bill[]>([]);
  const [filters, setFilters] = useState<BillFilters>(INITIAL_FILTERS);
  const [loadingBills, setLoadingBills] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingUpcoming, setLoadingUpcoming] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBills = useCallback(async () => {
    setLoadingBills(true);
    setError(null);
    try {
      const data = await fetchBills({
        ...filters,
        page,
        per_page: PER_PAGE,
      });
      setBills(data.bills);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load bills");
    } finally {
      setLoadingBills(false);
    }
  }, [filters, page]);

  const loadStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const data = await fetchStats();
      setStats(data);
    } catch {
      // Stats failure is non-critical
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const loadCities = useCallback(async () => {
    try {
      const data = await fetchCities();
      setCities(data);
    } catch {
      // Cities failure is non-critical
    }
  }, []);

  const loadTopics = useCallback(async () => {
    try {
      const data = await fetchTopics();
      setTopics(data);
    } catch {
      // Topics failure is non-critical
    }
  }, []);

  const loadUpcoming = useCallback(async () => {
    setLoadingUpcoming(true);
    try {
      const data = await fetchUpcoming(12);
      setUpcomingBills(data);
    } catch {
      // Upcoming failure is non-critical
    } finally {
      setLoadingUpcoming(false);
    }
  }, []);

  // Load cities and topics once on mount
  useEffect(() => {
    loadCities();
    loadTopics();
  }, [loadCities, loadTopics]);

  // Load stats and upcoming on mount and when refreshKey changes
  useEffect(() => {
    loadStats();
    loadUpcoming();
  }, [loadStats, loadUpcoming, refreshKey]);

  // Load bills when filters, page, or refreshKey change
  useEffect(() => {
    loadBills();
  }, [loadBills, refreshKey]);

  // Reset to page 1 when filters change
  const handleFiltersChange = (newFilters: BillFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <StatsCards stats={stats} loading={loadingStats} />
      <UpcomingActions bills={upcomingBills} loading={loadingUpcoming} />
      <CollectionsSidebar />
      <Filters
        filters={filters}
        cities={cities}
        topics={topics}
        onChange={handleFiltersChange}
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
        perPage={PER_PAGE}
        onPageChange={setPage}
        loading={loadingBills}
      />
    </main>
  );
}

export default Dashboard;
