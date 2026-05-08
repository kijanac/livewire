import { getContext } from "svelte";
import type { WritableBox } from "svelte-toolbelt";

export type ToastTone = "error" | "info" | "success";

export interface ToastContextValue {
  showToast: (message: string, tone?: ToastTone) => void;
}

const TOAST_KEY = Symbol("toast");

export function setToastContext(value: ToastContextValue) {
  // setContext is called in the ToastProvider component
}

export function useToast(): ToastContextValue {
  // We'll use Svelte context when we build the Toast component
  // For now, return a noop
  return {
    showToast: (message: string) => console.warn("Toast not initialized:", message),
  };
}
