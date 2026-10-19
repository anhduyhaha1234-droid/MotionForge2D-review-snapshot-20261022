# S10 correction-round (C6x) evidence & verification playbook

Verified during C6C/C6D/C6E rounds (2026-09-01). Applies to PM-gated correction
cycles where Codex returns CHANGES_REQUESTED and the Manager runs a bounded
correction + exit gate. Companion to `pm-worker-orchestration` / autopilot rules.

## 1. Immutable before/after evidence (Codex P2 rule)

- `output/s10/<round>/manager/prep/before/<case-name>/**` written BEFORE worker
  dispatch; NEVER rewrite after the worker starts (Codex flags overwritten prep
  evidence as P2 evidence-integrity finding).
- Post-fix runs write to `after/<case-name>/**` with NEW filenames (copy the
  script, `sed 's/result_before_X/result_after_X/g'`) — never reuse paths.
- Before-scripts assert the CONTRACT and are EXPECTED to fail pre-fix: the
  failing asserts + `result_before_*.json` ARE the defect record. Do not
  "repair" them; the worker owns the fix.
- If a check's semantics are wrong for the post-fix outcome (e.g. script
  requires replay success, but fail-closed 422 is the correct fix), fix only
  the AFTER copy: `C1 = (not ok) or (not mismatch)` (implication), then re-run
  and record both JSON + checks.

## 2. Repro-script mechanics (real route + real JobService + isolated SQLite)

- `tests/` is NOT a package → load helpers via importlib:
  ```python
  spec = importlib.util.spec_from_file_location(name, str(Path(ROOT)/"tests"/f"{name}.py"))
  mod = importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod)
  ```
- ROOT resolution: `next(p for p in Path(__file__).resolve().parents if (p/"tests"/"test_s10_full_apply_api.py").exists())`
  — NEVER `parents[N]` (breaks when evidence dirs nest deeper, hit in C6D).
- Evidence sidecars: `EVID = Path(__file__).resolve().parent`, write
  `result_*.json` there (script lives IN its case dir).
- Forced failure: `class _Boom(JobService): create_job raises` +
  `monkeypatch.setattr(deps, "_job_service", boom, raising=False)`; the route
  resolves the service via `deps._job_service` so this works through the real
  route.
- Fresh seed per test: `_, seed = _make_client(tmp_path, monkeypatch)`; path =
  `/api/v2/projects/<seed['project_id']>/full-apply`; body = `_payload(seed)`.
- DB rows via `factory()` + `text()` SELECT (job table cols: job_type, state,
  idempotency_key, input_generation, input_manifest_json, owner_type/owner_id,
  workspace_id).

## 3. TRUE-concurrency proof (Barrier must be inside the production call)

```python
barrier = threading.Barrier(2, timeout=30)
reached: list[str] = []
class _BarrierWrap(JobService):
    def create_job(self, *a, **k):
        barrier.wait()                 # rendezvous INSIDE real call
        reached.append(threading.current_thread().name)
        return super().create_job(*a, **k)
monkeypatch.setattr(deps, "_job_service", _BarrierWrap(...), raising=False)
# two THREADS, each with its own TestClient(app, raise_server_exceptions=False)
barrier_reached = len(reached) == 2 and not errors
```

Pitfalls hit:
- Barrier auto-resets after passing → re-calling `barrier.wait()` afterwards
  throws BrokenBarrierError — do NOT verify via a second wait.
- TestClient runs the app on an AnyIO portal thread → BOTH requests' create_job
  observe the SAME thread name → `len(set(reached))` under-counts; count
  ENTRIES (`len(reached) == 2`).
- Sequential A-then-B replay is NOT concurrent — Codex flags it (F4). Keep raw
  final DB rows in the JSON: `[(j['state'], j['input_generation']) ...]`.
- Known defect to expect pre-fix (C6D tree): two queued job rows with the same
  `s10_full_apply_job:<run-id>` key and `input_generation=None` (nullable
  unique-index hole; SQLite treats NULLs as distinct).

## 4. Model verification when the user questions the active model

- Worker cmdline scan (no `wmic|grep` one-liners — the agent hardline parser
  blocks them): write a `.ps1` (write_file) and run
  `powershell -ExecutionPolicy Bypass -File C:/.../scan.ps1`:
  ```powershell
  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'glm|deepseek-v4|hermes --resume' } |
    ForEach-Object { "{0} | {1}" -f $_.ProcessId, $_.CommandLine.Substring(0,150) }
  ```
  Quoting trap: a single quote inside a PS single-quoted string breaks the
  parse — drop `'` from regex char classes.
- Probe before dispatch: `hermes --resume <owner> --provider custom -m
  '<exact-model>' --yolo -z "reply exactly MODEL_PROBE_OK"` (TTFB 900); expect
  `MODEL_PROBE_OK` + `PROBE_EXIT=0`. `mkdir -p` the log dir BEFORE the `>`
  redirect (redirect to missing dir = silent loss, wrapper exit still 0/1).
- User "đổi hết sang model X" = ALSO switch the heartbeat cron
  (`hermes cron edit <id> --model X --provider Y`), verify via cronjob list.

## 5. Live UI / baked-origin check (T04B-style harness)

- `playwright.s10-ui.config.ts` + `globalSetup` seeding are REQUIRED (a bare
  custom config without seeding fails with `project S10-C6A-EXEC not found`).
- Ports MUST match the baked build origin: frontend build bakes
  `NEXT_PUBLIC_API_URL=http://localhost:8201` (2026-08 build); running the
  backend on 8212 gives "Failed to fetch" in the UI. Use `S10_BACKEND_PORT=
  8201 S10_FRONTEND_PORT=3000` (CORS allowlist) and fresh `MOTIONFORGE_ROOT`
  (e.g. `.../live/runtime4`). Ports auto-free after run.
- Focused subset: `--grep "submit from UI|cancel: visible enabled|retry:
  genuine retry|resume: interrupted leased"` → 8 cases (4 flows × desktop+
  mobile), ~6.1m.

## 6. J6 gate checklist (Manager, independent of worker REPORT)

- after-repros ×N (flip checks) → focused suite ×2 fresh short roots
  (`%TEMP%/mfcX_rN`) → full `tests/test_s10*.py` ×2 fresh roots → ruff
  `--select F` touched files → mypy touched prod → `git diff --check` →
  alembic 1 head → OpenAPI (paths/ops/distinct-ids/dups) → J1-v4 13/13 + EOL →
  broad-except sweep (verify each except: rollback+raise or documented
  read-path fallback; count 0 swallow) → porcelain attribution vs baseline →
  frozen-file SHA vs baseline (completion-CAS `s10_full_apply_jobs.py`) →
  frontend/harness/build hash-equal + build manifest validator
  (`output/s10/_build/frontend-build-manifest.json`: BUILD_ID, buildExitCode,
  scannedFileCount, matched8201, forbidden8888/8099, envContract).
- Retained evidence: hash-CONFIRM before retaining (pw-full.log,
  .last-run.json, c6-ui-evidence.jsonl, verticals' stdout logs); a "DIFF" from
  a naive `cat BUILD_ID` concatenation is a parsing artifact — compare the
  sha256sum lines directly.
