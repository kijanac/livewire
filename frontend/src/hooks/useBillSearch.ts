import { useState, useEffect, useCallback } from "react";
import { fetchBills } from "../api";
import type { Bill } from "../types";

export function useBillSearch() {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(false);

  const doSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchBills({ search: query, per_page: 20 });
      setResults(data.bills);
    } catch {
      // Search failure is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      doSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search, doSearch]);

  return { search, setSearch, results, loading };
}
