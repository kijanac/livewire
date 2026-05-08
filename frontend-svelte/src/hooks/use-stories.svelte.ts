import { fetchStories } from "@/api";
import type { StoryListResponse, StoryFilters } from "@/types";

const PER_PAGE = 20;

const DEFAULT_FILTERS: StoryFilters = {
  city: "",
  category: "",
  topic: "",
};

export function createStories() {
  let data = $state<StoryListResponse | null>(null);
  let loading = $state(true);
  let error = $state<Error | null>(null);
  let filters = $state<StoryFilters>({ ...DEFAULT_FILTERS });
  let page = $state(1);

  $effect(() => {
    const currentFilters = filters;
    const currentPage = page;
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchStories({ ...currentFilters, page: currentPage, per_page: PER_PAGE }, ctrl.signal)
      .then((res) => { data = res; })
      .catch((err) => {
        if (err.name !== "AbortError") error = err;
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  function updateFilters(next: StoryFilters) {
    filters = next;
    page = 1;
  }

  return {
    get stories() { return data?.stories ?? []; },
    get total() { return data?.total ?? 0; },
    get page() { return page; },
    set page(val: number) { page = val; },
    get perPage() { return PER_PAGE; },
    get filters() { return filters; },
    get loading() { return loading; },
    get error() { return error; },
    setFilters: updateFilters,
  };
}
