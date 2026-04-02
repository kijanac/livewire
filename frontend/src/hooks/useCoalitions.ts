import { useState, useEffect, useCallback } from "react";
import { fetchCoalitions } from "../api";
import type { CoalitionsResponse } from "../types";

export function useCoalitions() {
  const [data, setData] = useState<CoalitionsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchCoalitions();
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading };
}
