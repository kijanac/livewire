import { fetchBills } from "@/api";
import type { Bill } from "@/types";

export function createBillSearch() {
  let search = $state("");
  let results = $state<Bill[]>([]);
  let loading = $state(false);
  let error = $state<Error | null>(null);

  $effect(() => {
    const query = search;
    if (!query.trim()) {
      results = [];
      loading = false;
      error = null;
      return;
    }
    const ctrl = new AbortController();
    const timer = setTimeout(() => {
      loading = true;
      error = null;
      fetchBills({ search: query, per_page: 20 }, ctrl.signal)
        .then((data) => { results = data.bills; })
        .catch((err) => {
          if (err.name !== "AbortError") error = err;
        })
        .finally(() => { loading = false; });
    }, 300);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  });

  return {
    get search() { return search; },
    set search(val: string) { search = val; },
    get results() { return results; },
    get loading() { return loading; },
    get error() { return error; },
  };
}
