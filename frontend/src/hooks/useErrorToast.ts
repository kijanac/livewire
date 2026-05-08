import { useEffect } from "react";
import { useToast } from "@/components/Toast";

export function useErrorToast(error: unknown, label?: string): void {
  const { showToast } = useToast();
  useEffect(() => {
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
  }, [error, label, showToast]);
}
