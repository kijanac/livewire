<script lang="ts">
  import { setContext, getContext } from "svelte";
  import { cn } from "@/lib/utils";
  import X from "@lucide/svelte/icons/x";

  export type ToastTone = "error" | "info" | "success";

  interface ToastItem {
    id: string;
    message: string;
    tone: ToastTone;
  }

  export interface ToastContextValue {
    showToast: (message: string, tone?: ToastTone) => void;
  }

  const TOAST_KEY = Symbol("toast");
  const TOAST_DURATION_MS = 5000;

  const toneClasses: Record<ToastTone, string> = {
    error: "bg-destructive text-destructive-foreground",
    info: "bg-secondary text-secondary-foreground",
    success: "bg-emerald-600 text-white",
  };

  let { children }: { children: import("svelte").Snippet } = $props();

  let toasts = $state<ToastItem[]>([]);
  let counter = 0;
  let timers = new Map<string, ReturnType<typeof setTimeout>>();

  function dismiss(id: string) {
    toasts = toasts.filter((t) => t.id !== id);
    const timer = timers.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.delete(id);
    }
  }

  function showToast(message: string, tone: ToastTone = "info") {
    counter++;
    const id = `toast-${counter}`;
    toasts = [...toasts, { id, message, tone }];
    const timer = setTimeout(() => dismiss(id), TOAST_DURATION_MS);
    timers.set(id, timer);
  }

  $effect(() => {
    const currentTimers = timers;
    return () => {
      currentTimers.forEach((t) => clearTimeout(t));
      currentTimers.clear();
    };
  });

  const ctx: ToastContextValue = { showToast };
  setContext(TOAST_KEY, ctx);
</script>

{@render children?.()}

<div aria-live="polite" aria-atomic="true"
  class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full sm:w-auto">
  {#each toasts as t (t.id)}
    <div
      role={t.tone === "error" ? "alert" : "status"}
      class={cn(
        "pointer-events-auto flex items-start gap-3 rounded-lg shadow-lg px-4 py-3 text-sm animate-fade-up",
        toneClasses[t.tone]
      )}
    >
      <span class="flex-1 leading-snug break-words">{t.message}</span>
      <button type="button" onclick={() => dismiss(t.id)} aria-label="Dismiss notification"
        class="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity">
        <X class="h-4 w-4" />
      </button>
    </div>
  {/each}
</div>
