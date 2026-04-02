import { useState, useEffect, useCallback } from "react";
import { fetchBills } from "../api";
import type { Bill, BillFilters } from "../types";

const PER_PAGE = 25;

const INITIAL_FILTERS: BillFilters = {
  city: "",
  status: "",
  type_name: "",
  topic: "",
  urgency: "",
  search: "",
};

export function useBills(refreshKey: number) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<BillFilters>(INITIAL_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBills = useCallback(async () => {
    setLoading(true);
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
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    loadBills();
  }, [loadBills, refreshKey]);

  const handleFiltersChange = useCallback((newFilters: BillFilters) => {
    setFilters(newFilters);
    setPage(1);
  }, []);

  return {
    bills,
    total,
    page,
    perPage: PER_PAGE,
    filters,
    loading,
    error,
    setPage,
    setFilters: handleFiltersChange,
  };
}
