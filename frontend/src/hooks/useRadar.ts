import { useState, useEffect } from "react";
import { fetchRadar } from "../api";
import type { RadarResponse } from "../types";

export function useRadar() {
  const [radar, setRadar] = useState<RadarResponse | null>(null);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchRadar(selectedTopic || undefined, ctrl.signal)
      .then((res) => setRadar(res))
      .catch((err) => {
        if (err.name !== "AbortError") setError(err);
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [selectedTopic]);

  return { radar, selectedTopic, setSelectedTopic, loading, error };
}
