import { useState, useEffect } from "react";
import { fetchBills } from "../api";
import type { Bill } from "../types";

export function useBillSearch() {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!search.trim()) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }
    const ctrl = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      setError(null);
      fetchBills({ search, per_page: 20 }, ctrl.signal)
        .then((data) => setResults(data.bills))
        .catch((err) => {
          if (err.name !== "AbortError") setError(err);
        })
        .finally(() => setLoading(false));
    }, 300);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [search]);

  return { search, setSearch, results, loading, error };
}
