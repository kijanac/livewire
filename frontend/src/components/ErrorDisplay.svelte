<script lang="ts">
  import { Button } from "@/components/ui/button";
  import { Card, CardContent } from "@/components/ui/card";

  let { error }: { error: Error } = $props();
</script>

<div class="min-h-screen flex items-center justify-center bg-background p-4">
  <Card class="max-w-lg w-full">
    <CardContent class="p-6 sm:p-8">
      <h1 class="text-page-heading uppercase tracking-tight text-foreground mb-3">
        Something went wrong
      </h1>
      <p class="text-sm text-muted-foreground mb-4">
        An unexpected error occurred while rendering the page.
      </p>
      <pre class="text-xs font-[var(--font-mono)] bg-muted text-foreground p-3 rounded-md overflow-auto whitespace-pre-wrap break-words mb-4 max-h-48">
        {error.message}
      </pre>
      <Button onclick={() => window.location.reload()}>Reload</Button>
    </CardContent>
  </Card>
</div>
