import { useState, useEffect, useCallback } from "react";
import { fetchTopics } from "../api";

export function useTopics() {
  const [topics, setTopics] = useState<string[]>([]);

  const load = useCallback(async () => {
    try {
      const data = await fetchTopics();
      setTopics(data);
    } catch {
      // Topics failure is non-critical
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return topics;
}
