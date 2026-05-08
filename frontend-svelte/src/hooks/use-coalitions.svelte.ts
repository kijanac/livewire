import { fetchCoalitions } from "@/api";
import type { CoalitionsResponse } from "@/types";

export function createCoalitions() {
  let data = $state<CoalitionsResponse | null>(null);
  let loading = $state(true);
  let error = $state<Error | null>(null);

  $effect(() => {
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchCoalitions(ctrl.signal)
      .then((res) => { data = res; })
      .catch((err) => {
        if (err.name !== "AbortError") error = err;
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  return {
    get data() { return data; },
    get loading() { return loading; },
    get error() { return error; },
  };
}
