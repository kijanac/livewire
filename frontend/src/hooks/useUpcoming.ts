import { useState, useEffect, useCallback } from "react";
import { fetchUpcoming } from "../api";
import type { Bill } from "../types";

export function useUpcoming(refreshKey: number, limit: number = 12) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchUpcoming(limit);
      setBills(data);
    } catch {
      // Upcoming failure is non-critical
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return { bills, loading };
}
