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
  const [filters, setFilters] = useState<StoryFilters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchStories({
        ...filters,
        page,
        per_page: PER_PAGE,
      });
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    load();
  }, [load]);

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
    setPage,
    setFilters: updateFilters,
  };
}
