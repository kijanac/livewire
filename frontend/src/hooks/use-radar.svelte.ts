import { fetchRadar } from "@/api";
import type { RadarResponse } from "@/types";

export function createRadar() {
  let radar = $state<RadarResponse | null>(null);
  let selectedTopic = $state("");
  let loading = $state(true);
  let error = $state<Error | null>(null);

  $effect(() => {
    const topic = selectedTopic;
    const ctrl = new AbortController();
    loading = true;
    error = null;
    fetchRadar(topic || undefined, ctrl.signal)
      .then((res) => { radar = res; })
      .catch((err) => {
        if (err.name !== "AbortError") error = err;
      })
      .finally(() => { loading = false; });
    return () => ctrl.abort();
  });

  return {
    get radar() { return radar; },
    get selectedTopic() { return selectedTopic; },
    set selectedTopic(val: string) { selectedTopic = val; },
    get loading() { return loading; },
    get error() { return error; },
  };
}
