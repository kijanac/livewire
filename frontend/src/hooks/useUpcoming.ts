import { useState, useEffect } from "react";
import { fetchUpcoming } from "../api";
import type { Bill } from "../types";

export function useUpcoming(refreshKey: number, limit: number = 12) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchUpcoming(limit, ctrl.signal)
      .then((data) => setBills(data))
      .catch((err) => {
        if (err.name !== "AbortError") setError(err);
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [limit, refreshKey]);

  return { bills, loading, error };
}
