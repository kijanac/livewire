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
  jurisdiction_level: "",
};

export function useBills(refreshKey: number) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<BillFilters>(INITIAL_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchBills({ ...filters, page, per_page: PER_PAGE }, ctrl.signal)
      .then((data) => {
        setBills(data.bills);
        setTotal(data.total);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message ?? String(err));
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [filters, page, refreshKey]);

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
