# React → Svelte 5 Migration Scope

> **Inspired by:** `/Users/kijana/Documents/Code/transcriber` — a Svelte 5 + Tauri desktop app using the same shadcn/Tailwind/lucide stack.

---

## 1. Current State

### 1.1 Architecture

```
livewire/
├── frontend/          ← React 18 SPA (to be migrated)
│   ├── src/
│   │   ├── main.tsx          # React root + providers
│   │   ├── App.tsx           # Hash router + layout shell
│   │   ├── api.ts            # ~20 fetch functions
│   │   ├── types.ts          # ~30 interfaces
│   │   ├── index.css         # Tailwind 4 + theme
│   │   ├── lib/              # utils, bill-utils, visual-tokens
│   │   ├── hooks/            # 13 custom hooks (data fetching + state)
│   │   └── components/
│   │       ├── ui/           # 9 shadcn/ui components
│   │       └── *.tsx         # 11 app components + 12 briefing sub-components
│   └── package.json
├── backend/           ← Python/FastAPI (unchanged by migration)
└── docker-compose.yml
```

### 1.2 Component inventory (35 React files)

| Category | Count | Files |
|----------|-------|-------|
| UI primitives (shadcn) | 9 | button, card, dialog, sheet, badge, table, separator, select, input |
| App components | 11 | Dashboard, BillTable, RadarView, CoalitionView, StoriesView, CollectionView, Filters, StatsCards, UpcomingActions, BriefingPanel, AddBillModal, CollectionsSidebar, Toast, Spinner, ErrorBoundary |
| Briefing sub-components | 12 | BriefingShell, BriefingSummary, BriefingTimeline, BriefingCoalition, BriefingOrganizing, BriefingDocuments, BriefingReception, BriefingSimilar, BriefingNarrative, BriefingPower, BriefingNews, BriefingNotes |
| Hooks | 13 | useBills, useStats, useRadar, useCoalitions, useStories, useBriefing, useTopics, useCities, useBillSearch, useUpcoming, useCollection, useCollectionStubs, useErrorToast |
| Lib utilities | 3 | utils.ts (cn), bill-utils.ts, visual-tokens.ts |
| **Total** | **35 files** | |

### 1.3 Dependencies being replaced

| React | Svelte equivalent |
|-------|-------------------|
| `react` + `react-dom` | `svelte` |
| `@base-ui/react` (headless primitives) | `bits-ui` |
| `shadcn/ui` (shadcn CLI + components) | `shadcn-svelte` |
| `lucide-react` | `@lucide/svelte` |
| `class-variance-authority` | `tailwind-variants` |
| `@vitejs/plugin-react` | `@sveltejs/vite-plugin-svelte` |
| `@types/react` + `@types/react-dom` | (none — Svelte has native TS) |

### 1.4 Dependencies that stay the same

`clsx`, `tailwind-merge`, `tw-animate-css`, Tailwind CSS 4, Vite, all font packages, `@types/node`, TypeScript.

### 1.5 Backend — unchanged

The Python FastAPI backend (`/api/*` endpoints) requires zero changes. The same `api.ts` fetch logic ports cleanly — only the caller side changes (hooks → `.svelte.ts` modules).

---

## 2. Library Migration Map

### 2.1 Headless UI primitives: `@base-ui/react` → `bits-ui`

Both are headless component libraries. The API surface is similar but not identical.

| React (`@base-ui/react`) | Svelte (`bits-ui`) | Notes |
|--------------------------|---------------------|-------|
| `<Button>` | `<Button.Root>` | bits-ui uses compound components |
| `<Select.Root>`, `<Select.Trigger>`, etc. | `<Select.Root>`, `<Select.Trigger>`, etc. | Very similar API |
| `<Dialog.Root>`, `<Dialog.Trigger>`, etc. | `<Dialog.Root>`, `<Dialog.Trigger>`, etc. | Nearly identical |
| (roll-your-own Sheet) | `<Sheet.Root>`, etc. | bits-ui provides Sheet |

**Action:** Regenerate all 9 shadcn UI components using `shadcn-svelte` CLI.

### 2.2 Icons: `lucide-react` → `@lucide/svelte`

Import path change only:
```diff
- import { RefreshCw } from "lucide-react"
+ import RefreshCw from "@lucide/svelte/icons/refresh-cw"
```

Every icon import uses the tree-shakeable path (`/icons/<kebab-case-name>`). The transcriber project uses this pattern throughout.

### 2.3 Variants: `class-variance-authority` → `tailwind-variants`

Both provide a `tv()` function with nearly identical API:
```ts
// React (CVA)
import { cva } from "class-variance-authority"
const buttonVariants = cva("base-classes", { variants: {...} })

// Svelte (TV)
import { tv } from "tailwind-variants"
const buttonVariants = tv({ base: "base-classes", variants: {...} })
```

Minimal porting effort — rename `cva` → `tv`, add `base:` key.

### 2.4 Class merging

Both projects use `clsx` + `tailwind-merge` via a `cn()` helper. This stays **identical**.

### 2.5 Tailwind CSS 4

The `@theme inline` block, CSS custom properties, and `@layer` definitions stay the same. The `@source` directive (used in transcriber) should be added to scan `.svelte` files:

```css
@source "./src/**/*.{ts,svelte}";
```

---

## 3. Component Model Migration

### 3.1 React hooks → Svelte runes + `.svelte.ts` modules

This is the biggest conceptual shift. React hooks become Svelte runes.

#### State
```ts
// React
const [bills, setBills] = useState<Bill[]>([]);
const [loading, setLoading] = useState(true);

// Svelte (.svelte.ts)
let bills = $state<Bill[]>([]);
let loading = $state(true);
```

#### Derived values
```ts
// React
const totalPages = useMemo(() => Math.ceil(total / perPage), [total, perPage]);

// Svelte
let totalPages = $derived(Math.ceil(total / perPage));
```

#### Side effects
```ts
// React
useEffect(() => {
  const ctrl = new AbortController();
  fetchBills({...}, ctrl.signal).then(setBills);
  return () => ctrl.abort();
}, [filters, page]);

// Svelte
$effect(() => {
  const ctrl = new AbortController();
  fetchBills({...}, ctrl.signal).then((d) => { bills = d; });
  return () => ctrl.abort();
});
```

#### Refs
```ts
// React
const counterRef = useRef(0);
counterRef.current += 1;

// Svelte
let counter = $state(0);
counter += 1;
// Or for DOM refs:
let el = $state<HTMLElement | null>(null);
// <div bind:this={el}>
```

#### Context
```ts
// React
const ToastContext = createContext<ToastContextValue | null>(null);
export function ToastProvider({ children }) { ... }
export function useToast() { return useContext(ToastContext); }

// Svelte
// In provider ancestor:
import { setContext } from "svelte";
setContext("toast", toastValue);

// In consumer:
import { getContext } from "svelte";
const toast = getContext<ToastContextValue>("toast");
```

### 3.2 Pattern: custom hooks → `.svelte.ts` modules

React custom hooks return objects with state + setters. Svelte equivalent: export a function that returns an object with `$state` fields. See transcriber's `use-native-file-bridge.svelte.ts` for the exact pattern:

```ts
// hooks/use-bills.svelte.ts
export function createBillsStore(refreshKey: () => number) {
  let bills = $state<Bill[]>([]);
  let loading = $state(true);

  $effect(() => {
    const key = refreshKey();
    // fetch...
  });

  return {
    get bills() { return bills; },
    get loading() { return loading; },
  };
}
```

**Key insight from transcriber:** Use getter-based returns (`get bills()`) to ensure reactivity propagates correctly when the store object is destructured or passed around. The transcriber project uses this pattern consistently.

### 3.3 Lazy loading

```tsx
// React
const BriefingPanel = lazy(() => import("./BriefingPanel"));
<Suspense fallback={<Spinner />}>
  <BriefingPanel />
</Suspense>

// Svelte
{#await import("./BriefingPanel.svelte") then { default: BriefingPanel }}
  <BriefingPanel />
{:catch}
  <ErrorFallback />
{/await}
```

Alternatively, use a manual pending/error wrapper component (Svelte doesn't have a built-in Suspense equivalent, but `{#await}` handles promise-based lazy loading).

### 3.4 Error boundaries

React's class-based Error Boundaries have no direct Svelte equivalent. Options:

1. **Per-component try/catch** in `$effect` blocks
2. **A wrapper component** using `{#await}` and `onerror`
3. **`<svelte:boundary>`** (Svelte 5, experimental — check availability)

The transcriber project doesn't use error boundaries at all. For livewire, the simplest approach is a wrapper component pattern:

```svelte
<script lang="ts">
  let { children } = $props();
  let error = $state<Error | null>(null);
</script>

{#if error}
  <ErrorDisplay message={error.message} onRetry={() => error = null} />
{:else}
  {@render children?.()}
{/if}
```

### 3.5 Hash-based routing

Svelte doesn't ship a router. The current app uses a simple `window.location.hash` + `hashchange` listener. This ports directly — no router library needed:

```ts
// routes.svelte.ts
let route = $state<Route>({ page: "radar" });

function syncRoute() {
  const hash = window.location.hash;
  // parse hash into route...
}

$effect(() => {
  syncRoute();
  window.addEventListener("hashchange", syncRoute);
  return () => window.removeEventListener("hashchange", syncRoute);
});

export function useRoute() {
  return {
    get route() { return route; },
  };
}
```

---

## 4. shadcn-svelte Component Migration

Every UI component should be regenerated with `shadcn-svelte` rather than manually ported. The CLI generates idiomatic Svelte 5 components using bits-ui.

```bash
# From transcriber's setup:
npx shadcn-svelte@latest add button
npx shadcn-svelte@latest add card
npx shadcn-svelte@latest add dialog
npx shadcn-svelte@latest add sheet
npx shadcn-svelte@latest add badge
npx shadcn-svelte@latest add table
npx shadcn-svelte@latest add separator
npx shadcn-svelte@latest add select
npx shadcn-svelte@latest add input
```

**Note on Table:** shadcn-svelte's table is structural (HTML-based), not a headless component. It outputs `<table>` elements directly, which matches how livewire already uses it.

**Note on Sheet:** shadcn-react doesn't have a Sheet; livewire uses a custom `sheet.tsx`. shadcn-svelte **does** provide a Sheet component via bits-ui's `<Sheet.Root>`. The side panel (BriefingPanel, CollectionsSidebar) should use this instead of the custom implementation.

---

## 5. File-by-File Migration Plan

### Phase 1: Project scaffold (1-2 hours)

1. Create a new Svelte 5 project using `pnpm create vite@latest frontend-new --template svelte-ts`
2. Install dependencies matching transcriber's stack
3. Configure `vite.config.ts` (Svelte plugin, Tailwind, proxy, aliases)
4. Configure `svelte.config.js`, `tsconfig.json`, `components.json`
5. Port `index.css` (identical, add `@source` directive)
6. Port `lib/utils.ts` (identical)
7. Port `lib/bill-utils.ts` and `lib/visual-tokens.ts` (identical — no React in these)
8. Port `types.ts` (identical)
9. Port `api.ts` (identical — pure fetch, no React dependency)

**Files that copy verbatim:** `types.ts`, `api.ts`, `lib/utils.ts`, `lib/bill-utils.ts`, `lib/visual-tokens.ts`, `index.css` (with minor adjustments)

### Phase 2: UI components (1-2 hours)

Run `shadcn-svelte` to regenerate all 9 UI primitives. They'll land in `src/components/ui/` with the same directory structure.

**Manual work needed:**
- Replace `@base-ui/react` usages in `button.tsx` → bits-ui patterns (largely done by CLI)
- Replace `@base-ui/react` usages in `select.tsx` → bits-ui patterns (largely done by CLI)

### Phase 3: Core app shell (2-3 hours)

| File | Complexity | Notes |
|------|-----------|-------|
| `main.ts` | Low | `mount(App, { target })` — see transcriber's `main.ts` |
| `App.svelte` | Medium | Hash router, nav, sync button. Port all JSX to Svelte template syntax. `lazy` → `{#await import()}` |
| `Toast.svelte` | Medium | Context → `setContext`/`getContext`. `useRef` counter → `$state`. Transitions built-in |
| `Spinner.svelte` | Low | Pure SVG, nearly identical |
| `ErrorBoundary.svelte` | Medium | Class component → rune-based wrapper |

**Key concerns for App.svelte:**
- `lazy()` + `<Suspense>` → `{#await import('./Foo.svelte')}` for each route, or wrap in a `<RouteLoader>` component
- `useHashRoute()` → `.svelte.ts` module with `$state` + `$effect`

### Phase 4: Hooks → .svelte.ts modules (3-5 hours)

Each hook becomes a factory function in a `.svelte.ts` file:

| React Hook | Svelte Module | Complexity |
|------------|---------------|------------|
| `useBills` | `bills.svelte.ts` | Medium — useEffect → $effect, AbortController pattern identical |
| `useStats` | `stats.svelte.ts` | Low |
| `useRadar` | `radar.svelte.ts` | Low |
| `useCoalitions` | `coalitions.svelte.ts` | Low |
| `useStories` | `stories.svelte.ts` | Low |
| `useBriefing` | `briefing.svelte.ts` | Medium — history management |
| `useTopics` | `topics.svelte.ts` | Low |
| `useCities` | `cities.svelte.ts` | Low |
| `useBillSearch` | `bill-search.svelte.ts` | Low |
| `useUpcoming` | `upcoming.svelte.ts` | Low |
| `useCollection` | `collection.svelte.ts` | Medium |
| `useCollectionStubs` | `collection-stubs.svelte.ts` | Low |
| `useErrorToast` | `error-toast.svelte.ts` | Low |

**Pattern for most hooks:**
```ts
// use-bills.svelte.ts
export function createBills(refreshKey: () => number) {
  let bills = $state<Bill[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    const key = refreshKey();
    const ctrl = new AbortController();
    loading = true;
    fetchBills({...}, ctrl.signal)
      .then(d => { bills = d.bills; error = null; })
      .catch(e => { if (e.name !== "AbortError") error = e.message; })
      .finally(() => loading = false);
    return () => ctrl.abort();
  });

  return {
    get bills() { return bills; },
    get loading() { return loading; },
    get error() { return error; },
  };
}
```

### Phase 5: App components (4-6 hours)

| React Component | Svelte Equivalent | Lines (approx) | Complexity |
|----------------|-------------------|----------------|------------|
| `Dashboard.tsx` | `Dashboard.svelte` | ~40 | Low |
| `BillTable.tsx` | `BillTable.svelte` | ~200 | **High** — complex JSX with conditional classes, map, onClick delegation, pagination |
| `Filters.tsx` | `Filters.svelte` | ~80 | Medium |
| `StatsCards.tsx` | `StatsCards.svelte` | ~40 | Low |
| `RadarView.tsx` | `RadarView.svelte` | ~150 | Medium |
| `CoalitionView.tsx` | `CoalitionView.svelte` | ~200 | Medium |
| `StoriesView.tsx` | `StoriesView.svelte` | ~100 | Medium |
| `CollectionView.tsx` | `CollectionView.svelte` | ~150 | Medium |
| `CollectionsSidebar.tsx` | `CollectionsSidebar.svelte` | ~100 | Medium — use shadcn-svelte Sheet |
| `UpcomingActions.tsx` | `UpcomingActions.svelte` | ~60 | Low |
| `AddBillModal.tsx` | `AddBillModal.svelte` | ~80 | Medium — use shadcn-svelte Dialog |
| `BriefingPanel.tsx` | `BriefingPanel.svelte` | ~80 | Medium |

### Phase 6: Briefing sub-components (3-4 hours)

All 12 briefing sub-components follow a consistent pattern: receive props, display structured data. Porting is mechanical.

| Component | Complexity |
|-----------|------------|
| `BriefingShell` | Low |
| `BriefingSummary` | Low |
| `BriefingTimeline` | Low |
| `BriefingCoalition` | Low |
| `BriefingOrganizing` | Low |
| `BriefingDocuments` | Low |
| `BriefingReception` | Low |
| `BriefingSimilar` | Low |
| `BriefingNarrative` | Low |
| `BriefingPower` | Medium — vote bars, action list |
| `BriefingNews` | Low |
| `BriefingNotes` | Low |

---

## 6. JSX → Svelte Template Syntax Cheatsheet

### Conditional rendering
```tsx
// React
{loading ? <Spinner /> : <Content />}
{error && <Alert>{error}</Alert>}

// Svelte
{#if loading}<Spinner />{:else}<Content />{/if}
{#if error}<Alert>{error}</Alert>{/if}
```

### Lists
```tsx
// React
{bills.map((bill, i) => (
  <TableRow key={bill.id} style={{ animationDelay: `${i * 30}ms` }}>
    <TableCell>{bill.title}</TableCell>
  </TableRow>
))}

// Svelte
{#each bills as bill, i (bill.id)}
  <TableRow style="animation-delay: {i * 30}ms">
    <TableCell>{bill.title}</TableCell>
  </TableRow>
{/each}
```

### Event handlers
```tsx
// React
<button onClick={() => handleClick(bill.id)}>
<button onClick={(e) => { e.stopPropagation(); openUrl(); }}>

// Svelte
<button onclick={() => handleClick(bill.id)}>
<button onclick={(e) => { e.stopPropagation(); openUrl(); }}>
```

### Class toggling
```tsx
// React
<div className={cn("base", isActive && "active")}>

// Svelte
<div class={cn("base", isActive && "active")}>
```

### Inline styles
```tsx
// React
<div style={{ animationDelay: `${i * 30}ms` }}>

// Svelte
<div style="animation-delay: {i * 30}ms">
```

### Props
```tsx
// React (type + destructure in function)
function BillTable({ bills, loading }: BillTableProps) {

// Svelte 5 ($props rune)
let { bills, loading }: Props = $props();
```

### Children / slots
```tsx
// React
function Card({ children }: { children: ReactNode }) {
  return <div>{children}</div>;
}

// Svelte (default slot)
<script>
  let { children }: { children: Snippet } = $props();
</script>
<div>{@render children?.()}</div>

// Or multiple named slots:
// <Card><svelte:fragment slot="header">Title</svelte:fragment></Card>
```

### Forwarding refs
```tsx
// React
const ref = useRef<HTMLButtonElement>(null);
<button ref={ref}>

// Svelte
let ref = $state<HTMLButtonElement | null>(null);
<button bind:this={ref}>
```

---

## 7. Edge Cases & Gotchas

### 7.1 AbortController + $effect timing
Svelte's `$effect` re-runs when dependencies change. The cleanup function handles AbortController cleanup automatically. This matches React's `useEffect` cleanup pattern exactly — no change needed.

### 7.2 Hash routing & Svelte's reactive system
The hashchange listener inside `$effect` must NOT trigger a re-run. Make sure route changes happen via state assignment, not by triggering `$effect` dependencies. Use the pattern from section 3.5.

### 7.3 Stagger animations
`staggerDelay(i, ROW_STAGGER_MS)` returns an object `{ animationDelay: '...' }`. In Svelte templates, inline styles are strings:
```svelte
<!-- React -->
style={staggerDelay(i, ROW_STAGGER_MS)}

<!-- Svelte -->
style="animation-delay: {i * ROW_STAGGER_MS}ms"
```

### 7.4 `bind:this` for DOM refs
Unlike React's `useRef`, Svelte's `bind:this` doesn't survive between component mount/unmount cycles gracefully in all cases. For the BriefingPanel scroll-to-top behavior, use `tick()` or direct DOM queries on mount.

### 7.5 Two-way binding for form inputs
Svelte's `bind:value` replaces React's controlled input pattern with `value` + `onChange`. This simplifies Filters, AddBillModal, and the timestamp interval input significantly.

### 7.6 `@base-ui/react` → `bits-ui` API differences
While both are headless, bits-ui uses the compound component pattern more aggressively (e.g., `Button.Root` vs `Button`). The shadcn-svelte CLI generates idiomatic wrappers, so this only matters if customizing the primitives directly.

### 7.7 Transition lifecycle
React's `useEffect` with cleanup (`return () => {}`) maps to Svelte's `$effect` with cleanup. React's `useLayoutEffect` maps to `$effect.pre`. The latter is rarely needed.

---

## 8. Testing Strategy

Since this is a full framework migration, manual QA should be the primary verification:

1. **Phase-by-phase testing:** After each phase, run `pnpm dev` and verify the ported components render
2. **API parity:** All API calls should produce the same requests/receive the same responses (backend is unchanged)
3. **Visual comparison:** Compare screenshots between old React and new Svelte builds
4. **Interaction testing:** Click through all nav, filters, pagination, collections CRUD, briefing panel navigation

### Key test scenarios
- Bill table: filtering, pagination, clicking rows to open briefing
- Briefing panel: all 12 sections render, back/forward navigation works
- Radar view: cluster expansion, bill clicks
- Coalitions view: topic expansion, city alignment bars
- Stories view: filtering, pagination
- Collections: create, rename, add/remove bills, delete
- Dashboard: stats cards, upcoming actions, refresh button
- Toast notifications: error, success, auto-dismiss
- Sync/ingest: trigger refresh, display results

---

## 9. Effort Estimate

| Phase | Task | Estimated Hours |
|-------|------|-----------------|
| 1 | Scaffold + copy verbatim files | 1-2 |
| 2 | shadcn-svelte UI components | 1-2 |
| 3 | App shell (main, App, Toast, Spinner, ErrorBoundary) | 2-3 |
| 4 | Hooks → .svelte.ts modules (13 files) | 3-5 |
| 5 | App components (12 files) | 4-6 |
| 6 | Briefing sub-components (12 files) | 3-4 |
| 7 | Integration testing & polish | 3-5 |
| **Total** | | **17-27 hours** |

---

## 10. What Stays the Same

- **Backend** — zero changes
- **All CSS** — identical Tailwind 4 theme, animations, typography utilities
- **All API logic** — `api.ts` copies verbatim
- **All TypeScript types** — `types.ts` copies verbatim
- **All utility functions** — `lib/utils.ts`, `lib/bill-utils.ts`, `lib/visual-tokens.ts` copy verbatim
- **Docker setup** — no changes needed
- **Vite proxy config** — identical
- **Fonts** — identical (Fraunces, Plus Jakarta Sans, DM Mono)
- **All Tailwind classes** — identical across every component
