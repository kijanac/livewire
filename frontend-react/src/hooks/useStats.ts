import { useState, useEffect } from "react";
import { fetchStats } from "../api";
import type { StatsResponse } from "../types";

export function useStats(refreshKey: number) {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchStats(ctrl.signal)
      .then((res) => setStats(res))
      .catch((err) => {
        if (err.name !== "AbortError") setError(err);
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [refreshKey]);

  return { stats, loading, error };
}
