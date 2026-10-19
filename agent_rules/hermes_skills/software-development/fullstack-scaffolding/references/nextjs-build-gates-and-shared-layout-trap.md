# Next.js App Router build failure: the error names a route, the culprit can be a shared layout

Verified 2026-09-23 on a FastAPI + Next.js App Router product tree (`frontend/`), while fixing a
candidate whose **production build produced no working app at all**.

## The trap

The build reported:

```
useSearchParams() should be wrapped in a suspense boundary at page "/apply"
(missing-suspense-with-csr-bailout)
```

The natural (wrong) reading is "fix `/apply`". The actual culprit was
`frontend/src/components/layout/AppNav.tsx` — a component rendered by the **shared `(app)/` layout**.
Next.js prerenders every static route under `(app)/`, so a bare `useSearchParams()` in a layout-level
component aborts the prerender of **whichever route happens to be prerendered first** and the message
names that route, not the component.

Read the diff before believing the filename in the error.

## Fix shape that was accepted (minimal, 1 file, +30/−3)

Isolate the hook and wrap it, keeping the prerendered shell identical:

```tsx
export function AppNav() {
  // A static prerender has no query string, so a null-params sidebar IS the
  // correct server-rendered shell — the fallback is not a degraded state.
  return (
    <Suspense fallback={<AppNavSidebar projectId={null} videoItemId={null} />}>
      <AppNavWithQueryParams />
    </Suspense>
  );
}

function AppNavWithQueryParams() {
  const params = useSearchParams();
  return <AppNavSidebar projectId={params.get("project")} videoItemId={params.get("video")} />;
}

function AppNavSidebar({ projectId, videoItemId }: { projectId: string | null; videoItemId: string | null }) {
  const pathname = usePathname();   // prerender-safe, keeps its server output
  // …
}
```

Design notes worth keeping: choose the fallback deliberately (here: the correct static shell, so the
prerender is *right* rather than merely non-failing), and leave hooks that are prerender-safe
(`usePathname`, `useQuery` with a static `staleTime`) outside the boundary so their server-rendered
output is unchanged.

## Gate selection for a UI-only change

A commit that touches **0 Python files** is not gated by pytest. Check the language mix first
(`git show --name-only HEAD | grep -c '\.py$'`), then pick the real gates. The set that was accepted
for a frontend-only commit, each with its own exit code recorded:

| Gate | Evidence |
|---|---|
| `npx next build` (after `rm -rf .next`) | exit 0, static-page count printed (12/12) |
| `npx tsc --noEmit` | exit 0 |
| `npx eslint <patched files>` and `npx eslint <test dir>` separately | exit 0 each |
| `npx playwright test` for the three UI states (blocked / success / reopen) | exit 0, 3/3 |
| a **scoped** pytest run over the backend surface those states call over HTTP | exit 0, N passed |

Two habits that made this verifiable:

- **Record the exit code per gate** (`FINAL_BUILD_EXIT=0`, `TSC_EXIT=0`, …). A UI gate list without
  exit codes is prose, not evidence.
- Keep a **regression control**: even when pytest is not the acceptance gate, run a narrow suite over
  the backend the UI actually calls, isolated from the user's DB
  (`MOTIONFORGE_ROOT` / a per-test temp root). It costs a couple of minutes and catches collateral
  damage the build cannot see.
- Re-run the state test with `--repeat-each=2` at least once for flake confidence.

A worker note this session captured well, worth reusing verbatim in a packet: *"this commit changes 0
Python files, so pytest is not the acceptance gate of this task — the real gates are `next build` plus
the three UI states; I still ran a scoped pytest as a regression control."*

## Cosmetic-only diffs still need the diff read

The commit above changed **one** source file while the packet had listed six patch-only targets. That
is not a scope shortfall — it is evidence the diagnosis was right: the other five pages only *consume*
the fixed component. Verify by reading the diff (`grep -rn useSearchParams frontend/src` plus the
`Suspense` boundary check) before questioning why untouched files stayed untouched.

## Dependency discipline

A UI fix must not move the toolchain: confirm the commit touched **no** `package.json`,
`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` or `next.config.*` unless the packet explicitly
authorizes it. One `grep` over `git show --name-only HEAD` proves it.
