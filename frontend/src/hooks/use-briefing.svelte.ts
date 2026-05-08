import { fetchBriefing } from "@/api";
import type { BillBriefing } from "@/types";

const HISTORY_LIMIT = 20;

export function createBriefing(initialBillId: number) {
  let currentBillId = $state(initialBillId);
  let history = $state<number[]>([]);
  let briefing = $state<BillBriefing | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    const id = currentBillId;
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchBriefing(id, ctrl.signal)
      .then((res) => { briefing = res; })
      .catch((err) => {
        if (err.name !== "AbortError") {
          error = "Couldn't load this briefing. Try again.";
        }
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  function navigateTo(id: number) {
    history = [...history, currentBillId].slice(-HISTORY_LIMIT);
    currentBillId = id;
  }

  function goBack() {
    const prev = history[history.length - 1];
    if (prev !== undefined) {
      history = history.slice(0, -1);
      currentBillId = prev;
    }
  }

  return {
    get currentBillId() { return currentBillId; },
    get history() { return history; },
    get briefing() { return briefing; },
    get loading() { return loading; },
    get error() { return error; },
    navigateTo,
    goBack,
  };
}
