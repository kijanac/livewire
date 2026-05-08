import { useState, useEffect } from "react";
import { fetchTopics } from "../api";

export function useTopics() {
  const [topics, setTopics] = useState<string[]>([]);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchTopics(ctrl.signal)
      .then((data) => setTopics(data))
      .catch((err) => {
        if (err.name !== "AbortError") console.error("fetchTopics failed", err);
      });
    return () => ctrl.abort();
  }, []);

  return topics;
}
