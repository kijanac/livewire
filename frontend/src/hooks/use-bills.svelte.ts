import { fetchBills } from "@/api";
import type { Bill, BillFilters } from "@/types";

const PER_PAGE = 25;

const INITIAL_FILTERS: BillFilters = {
  city: "",
  status: "",
  type_name: "",
  topic: "",
  urgency: "",
  search: "",
  jurisdiction_level: "",
};

export function createBills(refreshKey: () => number) {
  let bills = $state<Bill[]>([]);
  let total = $state(0);
  let page = $state(1);
  let filters = $state<BillFilters>({ ...INITIAL_FILTERS });
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    const key = refreshKey();
    const currentFilters = filters;
    const currentPage = page;
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchBills({ ...currentFilters, page: currentPage, per_page: PER_PAGE }, ctrl.signal)
      .then((data) => {
        bills = data.bills;
        total = data.total;
      })
      .catch((err) => {
        if (err.name !== "AbortError") error = err.message ?? String(err);
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  function handleFiltersChange(newFilters: BillFilters) {
    filters = newFilters;
    page = 1;
  }

  return {
    get bills() { return bills; },
    get total() { return total; },
    get page() { return page; },
    set page(val: number) { page = val; },
    get perPage() { return PER_PAGE; },
    get filters() { return filters; },
    get loading() { return loading; },
    get error() { return error; },
    setFilters: handleFiltersChange,
  };
}
