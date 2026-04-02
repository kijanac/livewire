import { useState, useEffect, useCallback } from "react";
import { fetchStats } from "../api";
import type { StatsResponse } from "../types";

export function useStats(refreshKey: number) {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchStats();
      setStats(data);
    } catch {
      // Stats failure is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return { stats, loading };
}
