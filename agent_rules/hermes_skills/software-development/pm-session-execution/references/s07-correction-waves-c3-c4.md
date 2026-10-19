# S07 correction waves C3/C4 — finding/evidence trail (2026-08-22)

Session-level detail behind `correction-cycle-lessons.md` §15–§19.
Worktree: MotionForge2D-worktrees/s08-integration @ a43b20da (unchanged across
all waves). Owner sessions: T01 20260821_011252_8f17a1, T02
20260821_044658_7fde0f, T03 20260821_051414_184fd2.

## Wave C3 (Codex CHANGES_REQUESTED → resolved, manager-verified 06:52+07)

P1 fail-open authority:
- app/persistence/project_cast.py ~L302: `except Exception: current_gen = None`
  after the typed RoleNotFoundError branch. Contract of
  ObjectIntelligenceRepository.current_generation() (object_intelligence.py
  L348-369): returns str ALWAYS ("1" when no completed job) or raises
  RoleNotFoundError — so the broad catch had no legitimate case left.
- Worker fix: broad catch removed (comment explains fail-closed); only
  RoleNotFoundError → workspace_mismatch CompatibilityResult remains.
- New regression test tests/test_s07_project_cast_api.py L1251+:
  monkeypatch current_generation to raise RuntimeError("authority backend
  exploded"); assert resp.status_code >= 500; DB rows == [] via real session
  query; idempotency key still free; retry with SAME key succeeds.
- Evidence: output/s07-t01-c3/20260822_054741/{prefix_regression.log (FAILED
  pre-fix), postfix_regression.log (PASS)}.

P2 weak generation assertions in tests/test_s07_cast_compatibility.py:
- L350/L357 `assert curN == "1" or curN == "2"`; L376/379/410 `if cur == "2":`
  with pass-else at L384/L415. All replaced with exact "2" asserts built on
  deterministic seeds (fixed source SHA + completed DISCOVER_OBJECTS jobs).

Manager independent gates (temp roots s07c3mg_*, basetemp s07c3mg_bt*, DB_URL
unset, -p no:cacheprovider):
- Gate A focused 6-file T01: 64 passed (47.0s)
- Gate B full 9-file S07: 83 passed (63.2s) = Codex baseline 82 + 1 regression
- Gate C authority cluster (object_intelligence_domain, A02 c2/c3/r1c1,
  structural-evidence ×3, object-extraction ×3): 321 passed (4m21s)
- Gate D: ruff/mypy clean, alembic single b2c3d4e5f6a7b, protected hashes
  exact (channels.json dd7aae26…b555, motionforge.db 311296 B), ports clean.

Attribution audit note: tests/test_s11_original_audio_acceptance.py changed
inside the worker window but was untracked (`??`) S11-lane work by its own
owner; worker transcript had zero mentions of "s11". Not a violation.

## Wave C4 findings (verified by manager probe 10:58+07, dispatch 11:00)

P1a client-controlled workspace (probe = ground truth):
```
python - <<'EOF'
from fastapi.testclient import TestClient
from app.api.app import app
spec = TestClient(app).get("/openapi.json").json()
for path, ops in spec["paths"].items():
    if "project-cast" not in path: continue
    for method, op in ops.items():
        for p in op.get("parameters", []):
            print(method.upper(), path, p["name"], p["in"])
EOF
```
→ 20 operations expose `workspace_id (in=query)` because handlers declare
`workspace_id: str = WORKSPACE_ID` as a normal parameter (FastAPI turns any
defaulted scalar param into a query parameter — the default does NOT make it
server-owned). Fix direction: drop from signatures, use constant inside body;
regression = OpenAPI assert + adversarial ?workspace_id=<other-real-ws>.

P1b cross-workspace existence oracle:
- project_cast.py L466-478: natural_existing lookup filters only
  (project_id, object_role_id) — no workspace_id. Occupied pair in another
  workspace → 409 "already exists"; unoccupied → falls through to
  compatibility → workspace_mismatch. Response difference leaks existence.
- Note: idempotency-key lookup (L455-462) IS correctly workspace-scoped —
  mirror that pattern onto the natural lookup.

P2 (T02 lane) tautology at tests/test_s07_cast_compatibility.py L492:
`assert "workspace_mismatch" in j["reasons"] or "generation" in str(...) or
not j["compatible"]` — third disjunct makes it unfalsifiable.

## Manager dispatch mechanics that worked (both waves)
- Prompt file in Temp (C:/Users/Admin/AppData/Local/Temp/s07_cN_worker_prompt.txt)
  with: frozen guard block (HEAD/dirty/protected hashes), exclusive write-set,
  per-finding file:line evidence + expected fix + regression spec, numbered
  acceptance criteria, self-run gate list with EXACT env prefix
  (`env -u MOTIONFORGE_DATABASE_URL MOTIONFORGE_ROOT=... MOTIONFORGE_QA_MODE=1
  python -m pytest ... -p no:cacheprovider --basetemp=C:/Users/Admin/AppData/
  Local/Temp/<unique>`), model/route policy with BLOCKED_MODEL_ROUTE stop,
  timestamp rules (+07:00 real, UTC=local−7h), TASK_SUBMITTED-then-stop.
- Dispatch: hermes.exe chat --resume <owner> --provider custom --model alpha
  -q "$(cat prompt)" --yolo --pass-session-id --max-turns 150 --source tool >
  output/<task>-c<N>/<ts>_worker-c<N>.log 2>&1  (background + notify).
- Resume pause: "Preflight compression ~200k tokens" for several minutes is
  normal compaction, not a hang.
- Watchdog: extend WATCH_GLOBS with the new wave's glob BEFORE launch;
  STALL_SECS=900 to avoid false alarms during long silent Playwright runs.
