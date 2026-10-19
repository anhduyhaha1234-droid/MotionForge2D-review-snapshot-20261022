# FastAPI error-path publish UX — worked example (MotionForge S06-T05)

Recipe for frontend interaction tests around a FastAPI mutation with CAS
(revision) semantics, surfaced honestly in the UI. Proven on the MotionForge
2D "Pack Review & Publish" UX; adapt endpoint names/fields.

## Backend contract (approved, do not re-design)

- `POST /api/v2/characters/versions/{version_id}/publish` body `{revision: int}`.
- 200 → version DTO (status `published`, bumped `revision`).
- 404 unknown version; 409 stale revision (`detail` is a plain string:
  `"CAS revision mismatch: expected 2, got 1"`); 422 invalid pack with
  `detail: {message, missing_slots: [...], errors: [...]}`.
- Read-only validation: `GET .../versions/{version_id}/validation` →
  `{status, complete, missing_slots, errors}` — SAME validator as publish.

## Frontend client: unwrap the FastAPI error envelope

FastAPI wraps every error payload in `{"detail": <payload>}`. If the fetch
layer stores the raw body as the error's `detail`, the UI reads
`detail.message` as undefined and silently falls back. Unwrap ONCE in the
client:

```ts
export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;
  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// in apiFetch, on !res.ok:
const body: unknown = await res.json();
const detail =
  typeof body === "object" && body !== null && "detail" in body
    ? (body as { detail: unknown }).detail
    : body;
throw new ApiError(res.status, detail, `API ${res.status}: ${JSON.stringify(detail ?? "")}`);
```

UI handler then reads the typed payload directly:

```ts
if (error instanceof ApiError && error.status === 422) {
  const detail = error.detail as { message?: string; missing_slots?: string[]; errors?: string[] };
  // render detail.message + missing_slots labels + errors list
}
if (error instanceof ApiError && error.status === 409) {
  // show conflict message, invalidate list+validation queries (refresh state),
  // NEVER retry the mutation automatically
}
```

## UI pitfalls (both found by failing E2E tests)

1. **Feedback unmount bug**: the success banner lived INSIDE the publish
   panel, which is rendered only while the version is unpublished. On success
   the version flips to published → panel (and banner) unmounted → test saw no
   "Đã xuất bản" text. Fix: render the `role="status"` feedback at the parent
   level, outside the eligibility conditional.
2. **setState-in-effect**: clearing feedback when the selected version changed
   via `useEffect(() => setFeedback(null), [versionId])` failed the lint gate
   (`react-hooks/set-state-in-effect`). Fix: do it in the click handler
   (`selectVersion`), not an effect.

## Spec pattern (Playwright)

- `playwright.s06t05.config.ts`: `testMatch: /pack-publish-ux.*\.spec\.ts/`,
  `workers: 1`, `fullyParallel: false`, chromium only, baseURL :3010.
- Seeding: `output/qa-seed-s06-t05.py` uses the approved importer against the
  isolated QA DB (`MOTIONFORGE_ROOT=output/qa-root`) — real rows + real managed
  files. Idempotent; ALWAYS creates a fresh timestamped success target
  (`co_t05_<HHMMSS>`) and writes `output/qa-s06-t05/seed-state.json`; the spec
  reads it: `JSON.parse(readFileSync(path.resolve(__dirname, "../../output/qa-s06-t05/seed-state.json")))`.
- Success test publishes the fresh code (real mutation). Cancel/422/409 tests
  share a stable draft character (never mutated).
- Request counting helpers:

```ts
function countPublishPosts(page: Page, counter: { n: number }) {
  page.on("request", (req) => {
    if (req.method() === "POST" && /\/api\/v2\/characters\/versions\/[^/]+\/publish$/.test(req.url())) {
      counter.n += 1;
    }
  });
}
```

- 409 refresh assertion: capture `GET .../versions` count before the action,
  then `await expect.poll(() => versionGets.n).toBeGreaterThan(before)`.
- Assert the REAL server message, not the UI fallback: after the unwrap fix
  the UI shows `detail.message` from the intercepted body
  (`"Cannot publish pack version: validation failed"`), not
  `"Không thể xuất bản..."`.

## Structural visual QA probe (when the agent model has no vision)

`output/qa-probe-s06-t05.js` (run with `NODE_PATH=frontend/node_modules`):
for each viewport (1440×900, 390×844) evaluate:
- `document.documentElement.scrollWidth <= window.innerWidth` → no overflow;
- per `img`: `img.complete && img.naturalWidth > 0` (lazy images below the
  fold report false — scroll first or accept the caveat);
- publish button `getBoundingClientRect()` inside viewport + `disabled` flag.
Screenshots (`page.screenshot`) remain the pixel evidence for the PM review.
