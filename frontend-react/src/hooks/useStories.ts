import { useState, useEffect, useCallback } from "react";
import { fetchStories } from "../api";
import type { StoryListResponse, StoryFilters } from "../types";

const PER_PAGE = 20;

const DEFAULT_FILTERS: StoryFilters = {
  city: "",
  category: "",
  topic: "",
};

export function useStories() {
  const [data, setData] = useState<StoryListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [filters, setFilters] = useState<StoryFilters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchStories({ ...filters, page, per_page: PER_PAGE }, ctrl.signal)
      .then((res) => setData(res))
      .catch((err) => {
        if (err.name !== "AbortError") setError(err);
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [filters, page]);

  const updateFilters = useCallback((next: StoryFilters) => {
    setFilters(next);
    setPage(1);
  }, []);

  return {
    stories: data?.stories ?? [],
    total: data?.total ?? 0,
    page,
    perPage: PER_PAGE,
    filters,
    loading,
    error,
    setPage,
    setFilters: updateFilters,
  };
}
