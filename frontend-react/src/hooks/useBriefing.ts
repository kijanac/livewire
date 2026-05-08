import { useState, useEffect } from "react";
import { fetchBriefing } from "../api";
import type { BillBriefing } from "../types";

const HISTORY_LIMIT = 20;

export function useBriefing(initialBillId: number) {
  const [currentBillId, setCurrentBillId] = useState(initialBillId);
  const [history, setHistory] = useState<number[]>([]);
  const [briefing, setBriefing] = useState<BillBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    fetchBriefing(currentBillId, ctrl.signal)
      .then((res) => setBriefing(res))
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError("Couldn't load this briefing. Try again.");
        }
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [currentBillId]);

  const navigateTo = (id: number) => {
    setHistory((prev) => [...prev, currentBillId].slice(-HISTORY_LIMIT));
    setCurrentBillId(id);
  };

  const goBack = () => {
    const prev = history[history.length - 1];
    if (prev !== undefined) {
      setHistory((h) => h.slice(0, -1));
      setCurrentBillId(prev);
    }
  };

  return {
    currentBillId,
    history,
    briefing,
    loading,
    error,
    navigateTo,
    goBack,
  };
}
