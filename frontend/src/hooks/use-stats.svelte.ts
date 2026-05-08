import { fetchStats } from "@/api";
import type { StatsResponse } from "@/types";

export function createStats(refreshKey: () => number) {
  let stats = $state<StatsResponse | null>(null);
  let loading = $state(true);
  let error = $state<Error | null>(null);

  $effect(() => {
    const key = refreshKey();
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchStats(ctrl.signal)
      .then((res) => { stats = res; })
      .catch((err) => {
        if (err.name !== "AbortError") error = err;
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  return {
    get stats() { return stats; },
    get loading() { return loading; },
    get error() { return error; },
  };
}
