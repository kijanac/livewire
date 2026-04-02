import { useState, useEffect, useCallback } from "react";
import { fetchCities } from "../api";
import type { City } from "../types";

export function useCities() {
  const [cities, setCities] = useState<City[]>([]);

  const load = useCallback(async () => {
    try {
      const data = await fetchCities();
      setCities(data);
    } catch {
      // Cities failure is non-critical
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return cities;
}
