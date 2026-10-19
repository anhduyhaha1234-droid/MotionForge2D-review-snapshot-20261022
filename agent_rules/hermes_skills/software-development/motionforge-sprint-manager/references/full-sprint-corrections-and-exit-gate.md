# Full-sprint corrections, cascade & exit-gate playbook (S11-T02..T06, 2026-09-03)

Annotated second half of the S11 run (W4→W14 + sprint-exit), complementing
`s11-w1-w3-playbook.md`. 19/19 tasks MANAGER_VERIFIED, terminal
`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.

## 1. Defect cascade: enum contract violation (T02A-C1)

- Symptom at W6: T03D worker looped on "reason_code = ??? QC_REASON_CODES
  doesn't contain identity_drift". Actual T02A tuple was
  `{trajectory_drift, cut_drift, contact_break, z_order, clipping, identity,
  flicker, audio_timecode}` — wrong names, `edge_halo` MISSING, and an
  extra `audio_timecode`.
- Root cause: Manager verified T02A structure/tests but NOT the enum VALUES
  vs Decision B text (8 overlay codes exact names + 2 audio codes separate).
- Cascade: T06A1 media manifests (old names) → T02B test fixtures (old names).
  T06A2 and T03A happened to use correct names already. Cumulative gate
  failure counts: 28 → 26 → 0 after the three corrections.
- W6 handling: killed all 4 workers BEFORE they committed; recovered session
  IDs (`20260903_133051_*`) via `hermes sessions list`; ff'd each task branch
  to the fixed canonical (`c1a6777`); resumed exact sessions with a compact
  "context after fix" packet (enum list, new alembic head, their draft files
  need re-scan). All 4 finished with same-session continuity.

## 2. INT01 BLOCKED_REMOTE_DRIFT → authorized local-ahead

Sequence: W5 push (b34d801) → T02A-C1 merged locally, no push → INT01 T06A1-C1
merge halted: "remote b34d801 = push W5 của chính bạn; local 746b129 =
b34d801 + T02A-C1". Manager explicitly authorized local-ahead; INT01 merged,
then a single non-force ff push `b34d801..<tip>` closed it. Remote SHA was
self-originated — checked before waiving.

## 3. Session ID recovery after kill (Windows/Hermes CLI)

Killed `hermes chat -q` leaves no `session_id:` line. Recovery:
`hermes sessions list` (no workspace filter worked for killed runs) — match by
title (prompt first line). One wrong-ID resume happened (T03B resume used
T02B's session) → killed within seconds, no damage; lesson: always resolve IDs
from the list, never from memory/guess.

## 4. Exit-gate mypy correction round (9 errors / 6 files)

Findings: thresholds.py no-any-return + runner.py unused-ignore (T03A);
orchestrator.py unused-ignore + assignment (T03F); qc_checks_handler.py
arg-type _CancelFlag (T03G); qc_av_recheck.py dict arg-type (T04C);
qc_correction_bridge.py comparison-overlap + arg-type + missing-return (T04B).

- ff'd 5 branches to frozen canonical `15f4349`; dispatched 5 parallel
  resumes, each with its OWN finite matrix (bounded patch, no behavior change,
  verify own-file mypy + own tests + ruff F).
- Cross-file check trap: after T03F's fix, `mypy orchestrator.py` still showed
  thresholds/runner errors — those were T03A's unmerged branch, not T03F.
- All 5 merged (1 ff + 4 no-ff) → `python -m mypy <11 prod files>` on
  integrated HEAD → **Success**; affected 106/106 tests re-run green.

## 5. Exit gates that bit back (exact commands)

- Alembic: `python -m alembic -x db_url=sqlite:///<temp> upgrade head` —
  `MOTIONFORGE_DATABASE_URL` alone is refused ("No database URL configured").
  Downgrade must target `e11a02a2026f` (prev revision), not the current head
  (no-op trap). Then fk_check + integrity_check.
- OpenAPI no-removed: diff current paths vs T02B worker's
  `openapi_paths_before.txt` archive (263 paths) — additions only.
- Frontend: `npx next build --webpack` (Turbopack rejects junction
  node_modules); BUILD_ID captured; Playwright evidence in
  `%TEMP%/s11t04d_pw` + `s11t05b_pw`; canonical `.last-run.json` mtime 10:59 =
  pre-sprint staging artifact (attribute by mtime, not a leak).
- Protected: S10 route `5a6c7e86…`/test `e26a96dc…` unchanged; T01 engine+
  tests byte-identical; `original_audio_handler.py` hash changed = authorized
  T04C EXTEND (record as intended, re-ran 64/64 T01 regression).
- Leak: tasklist-based ffmpeg/ffprobe count = 0 at exit + T06C inner 15s
  window survivors [].

## 6. Coordination docs + final push

- Manager authored SESSION_REGISTRY + SPRINT_REPORT from evidence-root finals;
  INT01 copied them into canonical (`docs/pm/sessions/`,
  `docs/pm/sprints/`), committed as coordination bytes, single non-force push,
  verified `ls-remote == local` (`4d7ad81`).
- NEXT_REVIEW_PACKET.md (SHA recorded) maps 19 IDs + INT01 to
  session/model/worktree/branch/range/remote SHA, 14-wave ledger, write audit,
  protected hashes, gate evidence per item, notes (T04D −9-line Apply-link
  removal, reasoning_config=null RUNTIME_CONFIG_GAP, 1×502 retry), quiescence,
  zero S13.

## 7. Stale background-exit noise

After terminal, `[IMPORTANT: Background process ... completed]` notifications
keep arriving for every historical bash wrapper (hours old). Treat as noise;
respond one line, no action.