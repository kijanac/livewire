import { fetchTopics } from "@/api";

export function createTopics() {
  let topics = $state<string[]>([]);

  $effect(() => {
    const ctrl = new AbortController();
    fetchTopics(ctrl.signal)
      .then((data) => { topics = data; })
      .catch((err) => {
        if (err.name !== "AbortError") console.error("fetchTopics failed", err);
      });
    return () => ctrl.abort();
  });

  return {
    get topics() { return topics; },
  };
}
