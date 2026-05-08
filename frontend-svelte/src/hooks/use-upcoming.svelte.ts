import { fetchUpcoming } from "@/api";
import type { Bill } from "@/types";

export function createUpcoming(refreshKey: () => number, limit: number = 12) {
  let bills = $state<Bill[]>([]);
  let loading = $state(true);
  let error = $state<Error | null>(null);

  $effect(() => {
    const key = refreshKey();
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchUpcoming(limit, ctrl.signal)
      .then((data) => { bills = data; })
      .catch((err) => {
        if (err.name !== "AbortError") error = err;
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  return {
    get bills() { return bills; },
    get loading() { return loading; },
    get error() { return error; },
  };
}
