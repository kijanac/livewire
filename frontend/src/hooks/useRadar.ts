import { useState, useEffect, useCallback } from "react";
import { fetchRadar } from "../api";
import type { RadarResponse } from "../types";

export function useRadar() {
  const [radar, setRadar] = useState<RadarResponse | null>(null);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchRadar(selectedTopic || undefined);
      setRadar(data);
    } catch {
      setRadar(null);
    } finally {
      setLoading(false);
    }
  }, [selectedTopic]);

  useEffect(() => {
    load();
  }, [load]);

  return { radar, selectedTopic, setSelectedTopic, loading };
}
