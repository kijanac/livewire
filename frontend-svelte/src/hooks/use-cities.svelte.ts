import { fetchCities } from "@/api";
import type { City } from "@/types";

export function createCities() {
  let cities = $state<City[]>([]);

  $effect(() => {
    const ctrl = new AbortController();
    fetchCities(ctrl.signal)
      .then((data) => { cities = data; })
      .catch((err) => {
        if (err.name !== "AbortError") console.error("fetchCities failed", err);
      });
    return () => ctrl.abort();
  });

  return {
    get cities() { return cities; },
  };
}
