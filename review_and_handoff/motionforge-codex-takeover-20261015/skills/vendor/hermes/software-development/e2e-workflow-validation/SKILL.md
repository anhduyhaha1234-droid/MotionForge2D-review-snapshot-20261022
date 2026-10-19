---
name: e2e-workflow-validation
description: "Validate end-to-end workflows with real data and browser testing"
tags: [e2e, workflow, validation, browser, testing]
---

# E2E Workflow Validation

## When to Use

- Validating a complete user workflow from upload to output
- Testing browser-based UI with real backend
- Verifying that frontend and backend integrate correctly
- Running Playwright or browser automation tests
- Validating that output artifacts (video, JSON, images) are correct

## Workflow Validation Pattern

### 1. Define the Workflow Steps
List every step the user takes, from initial action to final output. Each step must have:
- Action (click, upload, navigate, wait)
- Expected result (status code, UI state, file existence)
- Verification command

### 2. Run Against Real Backend
Never mock the backend for E2E validation. Use TestClient for API-level E2E, or run the actual backend + frontend for browser E2E.

### 3. Verify Output Artifacts
For every output file the workflow produces:
- Check file exists at the expected path
- Verify file size > 0
- Run format-specific validation (ffprobe for video, json.parse for JSON, etc.)
- Compare key properties against input (resolution, fps, duration, audio)

### 4. Browser E2E with Playwright
For browser-based workflows:
- Install Playwright: `npm install -D @playwright/test`
- Create `playwright.config.ts` with base URL
- Write happy-path test that exercises the full UI workflow
- Write GPU workflow test with `@slow` marker for long-running tests
- Write coordinate validation test for canvas interactions
- Run with `npx playwright test`

### 5. Screenshot Documentation
Capture screenshots of each major screen state:
- `docs/screenshots/<milestone>/01_<screen>.png`
- Never use mockups — only real application screenshots
- Include error states

## Frontend Interaction Testing: Error Paths + Real Mutations

When the task calls for focused interaction tests (confirmation dialogs, success/refetch, 422, 409, disabled states, immutable states):

1. **Success/neutral paths use REAL backend mutations** — never mock the happy path. Seed real data through the app's own repository/importer (a Python seed script) so the UI operates on genuine rows/files. The user explicitly rejects mock data.
2. **Error paths (422/409/500) are exercised at the network boundary with `page.route` interception** — the only honest way to force a specific error response without corrupting shared data:
```ts
await page.route("**/api/v2/characters/versions/*/publish", async (route) => {
  if (route.request().method() !== "POST") return route.continue();
  await route.fulfill({
    status: 422,
    contentType: "application/json",
    body: JSON.stringify({ detail: { message: "...", missing_slots: [...], errors: [...] } }),
  });
});
```
3. **Assert exactly-one-attempt / no-silent-retry** by counting requests on `page.on("request", ...)` and asserting the counter after a settle (`page.waitForTimeout(1000)`). For a 409 that must refresh state, count `GET` list requests before/after and assert the counter grew (`expect.poll`).
4. **Fresh per-run state instead of destructive resets.** A success test that mutates (e.g., publishes) pollutes the target for reruns. Seed a NEW uniquely-coded entity per run (timestamped code), write its id/code to `output/qa-*/seed-state.json`, and have the spec read it via `readFileSync`. Reruns stay green with zero deletes — avoid `shutil.rmtree`-style resets in seeds (they trip approval gates and destroy evidence).
5. **Scope text assertions to their container** — `getByRole("button", { name: /Phiên bản v1/ }).getByText("Nháp", { exact: true })` instead of a bare `getByText("Nháp")` which can match a filter dropdown or a status badge elsewhere on the page.
6. **Structural visual QA fallback when the model can't see screenshots**: run a Playwright probe that evaluates `scrollWidth <= innerWidth` (no horizontal overflow), `img.complete && naturalWidth > 0` (images loaded — note `loading="lazy"` images below the fold report false until scrolled), and button `getBoundingClientRect()` visibility. Keep the PNGs as the pixel evidence for human review.

See `references/fastapi-error-path-publish-ux.md` for a full worked example (FastAPI publish UX: ApiError unwrap, confirmation/422/409/success specs, seed-state pattern).

## Playwright failure forensics: read trace.zip's network file FIRST (verified 2026-08-22)

When a Playwright run fails on an assertion like `submit-success` never appearing, do NOT guess
from DOM snapshots alone. Three approaches commonly fail before the right one:

1. `DEBUG=pw:api` — logs Playwright API calls only, NOT the app's fetch/XHR traffic. Dead end.
2. Manual reproduction with hand-started servers — a production Next.js bundle **bakes
   `NEXT_PUBLIC_API_URL` (and any other `NEXT_PUBLIC_*`) into `.next/` at BUILD time**, so a
   manually started `next start` with different env silently points at the wrong backend port;
   CORS/QA-mode mismatches produce a page that can't call the API at all ("Không đọc được trạng
   thái phân tích"). Your repro then measures your environment, not the defect.
3. ✅ **Re-run just the failing test with `--trace on`, then parse the trace zip** — it records
   every request/response including bodies:

```bash
npx playwright test --config=... -g "failing test" --project=desktop --trace on
python - <<'EOF'
import zipfile, json
z = zipfile.ZipFile("test-results/<failure-dir>/trace.zip")
for line in z.read("0-trace.network").decode("utf-8","replace").splitlines():
    if not line.strip(): continue
    try: e = json.loads(line)
    except Exception: continue
    snap = e.get("snapshot", {}); req = snap.get("request", {})
    url = req.get("url", "")
    if "<api-substring>" not in url: continue          # filter to the endpoints you care about
    resp = snap.get("response", {}) or {}; content = resp.get("content", {}) or {}
    sha = content.get("_sha1")
    print(req.get("method"), url[:100], "->", resp.get("status"))
    post = req.get("postData", {}) or {}
    if post.get("text"): print("  REQ:", post["text"][:280])
    if sha:                                            # response body stored under its sha1
        for n in z.namelist():
            if n.endswith(sha):
                print("  RES:", z.read(n).decode("utf-8","replace")[:240]); break
EOF
```

   This shows the exact request the UI made AND the server's response body (e.g. a `409 …already
   bound to a different cast mapping payload`) plus the *earlier* GETs that reveal state before the
   failing action (`"total":1` = a mapping already existed). One artifact answers both "what did the
   client send" and "what had the server already".

## Global-setup wipe failures are SILENT on Windows (extends residue pitfall #4)

- `shutil.rmtree(root, ignore_errors=True)` in a boot/global-setup script swallows EPERM while an
  old uvicorn still holds `motionforge.db` open. Seeding then runs against a STALE DB; with
  deterministic seed data (fixed UUIDs / idempotency keys derived from them) the first UI pin hits
  `409 idempotency key … already bound` from leftover rows, and the whole suite fails while the
  code is correct. Verify wipes loudly: after rmtree, assert the root is empty (or recreate it) and
  fail fast if files remain; make sure prior webServers are actually dead before wiping.
- Killing a background **bash wrapper does not kill its node child** on Windows: `next start` keeps
  listening after the shell exits. Find real owners via `netstat -ano | grep LISTENING | grep :<port>`
  → PID → `powershell Stop-Process -Id <pid> -Force`. Check ports are free before re-running.

## WebServer wrapper processes + multi-project matrices (verified 2026-08-22)

- **`os.execv` in a Playwright webServer/boot wrapper ORPHANS the server on Windows.** execv there
  spawns a NEW python process (different PID) and the wrapper exits, so Playwright's teardown kills
  the dead wrapper PID while uvicorn survives holding the app port + SQLite file. Symptom: reporter
  prints all results, then the runner hangs FOREVER after "N passed" (log mtime goes stale — detect
  via `stat -c %y log` vs current time instead of waiting blindly; results are already in
  `test-results/`). Three consecutive runs left three orphan listeners on :8004. Fix pattern for the
  wrapper: spawn the server with `subprocess.Popen`, block on `wait()`, forward SIGTERM/SIGINT to the
  child so teardown kills the real tree. After every local run, gate on
  `netstat -ano | grep LISTENING | grep :<port>` being EMPTY (`grep -c` returning 0 / exit-1 IS the
  green evidence here). Also avoid wrapping the runner in shell `timeout` under MSYS bash — it kills
  mid-run with EXIT=124; rely on playwright's own per-test timeout.
- **One test × N projects × ONE shared seeded DB = second-pass mutation conflicts.** When a config
  defines multiple projects (desktop + mobile) around the same spec, each test body executes once PER
  PROJECT against the same boot-seeded database. Any non-idempotent step (create mapping, publish,
  repin) passes on the first execution and 409s on the second (`idempotency key already bound`,
  natural-key exists) — so each lane passes standalone but the combined matrix fails mid-run. Either
  give every project its own temp root/DB, or make the flow re-runnable: per-test cleanup (list+delete
  pre-existing rows for the target keys) at the top plus explicit already-published/already-exists
  handling. Never "fix" this by shrinking lanes to width-only smoke tests.
- **A config that gained projects/tests AFTER acceptance evidence invalidates that evidence.** Old
  "2 passed" logs prove only the matrix that existed then; run the FULL current matrix before citing
  prior green. And reproduce failures with the SAME config file the evidence used — sibling configs
  with near-identical names can differ in webServer wiring (boot/seed script vs bare dev server) and
  send you chasing a fake "wipe never ran" root cause. Check file mtimes + the webServer command block
  first.

## Fail-open assertion patterns (review-blocking — verified S07-T03 real-vertical review 2026-08-21)

These shapes make a test PASS when the system under test is BROKEN. Treat any occurrence as a
CHANGES_REQUESTED finding, not a style nit:

1. **`if (response.ok()) { …asserts… }` around MANDATORY steps** — if the API call fails, the asserts
   are skipped and the test goes green while the feature never worked. Mandatory setup/write calls must
   be unconditional: `expect(res.ok()).toBeTruthy()` (or `expect(res.status()).toBe(201)`) BEFORE using
   the body.
2. **Direct incompatible write returning 2xx must FAIL the test immediately**:
   ```ts
   const direct = await request.post(`${API}/api/v2/project-cast`, { data: incompatPayload });
   expect([409, 422, 400]).toContain(direct.status()); // NOT: if (direct.ok()) { re-assert something else }
   ```
   Re-asserting "the evaluate endpoint says blocked" after an accepted write does not close the hole —
   the write boundary itself failed; the test must notice.
3. **Optional-looking setup chains** (`if (charRes.ok()) { const pv = await …; if (pvRes.ok()) {…} }`)
   silently drop the whole negative-path block when setup fails. Setup for a required scenario is
   required: fail hard on its status codes.
4. **Global-setup residue dependence**: seed helpers that don't wipe/recreate their temp root read a
   stale `seed.json` from a previous run (or crash on first run). Wipe + recreate the temp root inside
   globalSetup so every run is self-contained.
5. **Mobile viewport test ≠ mobile scenario**: asserting only `boundingBox().width <= 390` proves
   layout, not the workflow. The 390px lane must execute the same Scenario-I flow (pin → publish →
   isolation → stale-409) as desktop.
6. **Stale config pointing at deleted routes**: a playwright config whose webServer URL targets a
   removed harness page (`/test-s07-t03`) plus its old spec are obsolete — rewrite toward the real
   production route or merge into the real-vertical spec; never count them as acceptance evidence.

## UI Test Pitfalls

1. **Transient feedback must render OUTSIDE the conditional that unmounts on state change.** A success/error banner placed inside the panel that contains the triggering button disappears the moment the mutation's success changes state (e.g., the publish panel unmounts once the version becomes published — the "Đã xuất bản" message vanished). Render feedback at the parent level, independent of the eligibility conditional.
2. **Reset UI state in event handlers, not `useEffect`.** `react-hooks/set-state-in-effect` (newer react-hooks eslint rules) FAILS the lint gate for synchronous `setState` in an effect body (e.g., clearing feedback when the selection changes). Move the reset into the click handler that changes the selection.
3. **Stale dev servers masquerade as test failures.** A long-lived `next dev` server can hang (all `page.goto` time out) after heavy edit sessions — restart it (`npm run dev -- -p <port>`). Background uvicorn can also die silently; probe with `curl` before blaming the tests. Playwright failure dirs under `test-results/` show which tests actually failed vs hung.

## Common Pitfalls

1. **Using mock data for E2E validation** — E2E means real data, real backend, real browser. Mocks defeat the purpose.
2. **Not verifying output files** — a successful API response doesn't mean the output file is correct. Always run ffprobe/json.parse on the actual artifact.
3. **Browser testing without a running backend** — Playwright tests need both frontend and backend running. Start both before running E2E.
4. **Ignoring Playwright test failures** — if a Playwright test fails, diagnose the root cause (missing element, wrong selector, timing issue) rather than retrying blindly.
5. **Not testing error states** — E2E validation should include what happens when the user makes a mistake or the API returns an error.
6. **Screenshot placeholders** — screenshots must be from the real application, not mockups or generated images.

## Verification Checklist

- [ ] All workflow steps defined with expected results
- [ ] Backend running and healthy
- [ ] Frontend running and connected to backend
- [ ] Happy-path E2E test passes
- [ ] Output artifacts validated (file exists, non-zero size, format correct)
- [ ] Error states tested
- [ ] Screenshots captured for each major screen
- [ ] Playwright tests pass

## Ad-Hoc Server + Endpoint Verification

When no test suite exists, verify the full API surface with a subprocess-based approach using only stdlib (`urllib.request`):

```python
import subprocess, time, json, urllib.request, urllib.error

# 1. Start server as subprocess on a non-standard port
srv = subprocess.Popen(
    [python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18765"],
    cwd=project_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
time.sleep(4)  # wait for startup

# 2. Define API helper (no httpx/requests dependency)
def api(method, path, body=None):
    url = f"http://127.0.0.1:18765{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    resp = urllib.request.urlopen(req, timeout=120)
    return resp.status, json.loads(resp.read())

# 3. Verify route registration via OpenAPI introspection
status, spec = api("GET", "/openapi.json")
registered_paths = list(spec["paths"].keys())
# Assert all expected routes are present — catches import errors silently swallowed by FastAPI

# 4. Test each endpoint with real data
for endpoint, request_body, assertions in test_cases:
    status, body = api("POST", endpoint, request_body)
    assert status == 200
    for check in assertions:
        check(body)

# 5. Cleanup
srv.terminate()
srv.wait(timeout=5)
```

**Advantages:** No httpx/requests dependency, no TestClient, tests the real server process. The OpenAPI spec introspection catches routes that failed to register due to import errors.

**Key insight:** If an endpoint returns 405 Method Not Allowed, it likely wasn't registered — check OpenAPI spec first. If it returns 404 Not Found but other routes work, the route exists but the path doesn't match.

**Pitfall:** On Windows, `subprocess.Popen` with `stdout=PIPE` can deadlock if the output buffer fills. For long-running servers, redirect to a file or use `subprocess.DEVNULL`.

**Pitfall:** Port conflicts — check with `netstat -ano | grep <port>` before starting. Kill stale processes first.