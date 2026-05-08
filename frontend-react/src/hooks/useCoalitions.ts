import { useState, useEffect } from "react";
import { fetchCoalitions } from "../api";
import type { CoalitionsResponse } from "../types";

export function useCoalitions() {
  const [data, setData] = useState<CoalitionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchCoalitions(ctrl.signal)
      .then((res) => setData(res))
      .catch((err) => {
        if (err.name !== "AbortError") setError(err);
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, []);

  return { data, loading, error };
}
