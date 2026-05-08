import { getContext } from "svelte";
import type { ToastContextValue } from "@/components/ToastProvider.svelte";

const TOAST_KEY = Symbol("toast");

export function useToast(): ToastContextValue {
  return getContext<ToastContextValue>(TOAST_KEY);
}

export function useErrorToast(error: unknown, label?: string): void {
  const { showToast } = useToast();

  $effect(() => {
    if (!error) return;
    const prefix = label ?? "Something failed";
    let message: string;
    if (error instanceof Error && error.message) {
      message = `${prefix}: ${error.message}`;
    } else if (typeof error === "string" && error) {
      message = `${prefix}: ${error}`;
    } else {
      message = prefix;
    }
    showToast(message, "error");
  });
}
