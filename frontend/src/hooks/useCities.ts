import { useState, useEffect } from "react";
import { fetchCities } from "../api";
import type { City } from "../types";

export function useCities() {
  const [cities, setCities] = useState<City[]>([]);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchCities(ctrl.signal)
      .then((data) => setCities(data))
      .catch((err) => {
        if (err.name !== "AbortError") console.error("fetchCities failed", err);
      });
    return () => ctrl.abort();
  }, []);

  return cities;
}
