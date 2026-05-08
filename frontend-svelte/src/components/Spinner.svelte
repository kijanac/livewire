<script lang="ts">
  import { cn } from "@/lib/utils";

  let { class: className = "", size = 16 }: { class?: string; size?: number } = $props();
</script>

<svg
  class={cn("animate-spin", className)}
  style="width: {size}px; height: {size}px"
  viewBox="0 0 24 24"
  fill="none"
  aria-hidden="true"
>
  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
</svg>
