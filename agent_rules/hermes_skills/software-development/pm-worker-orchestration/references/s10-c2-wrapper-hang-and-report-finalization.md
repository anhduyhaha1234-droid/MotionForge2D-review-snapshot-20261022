# S10-C2 — wrapper hang + iteration-limit report-only pattern (verified 2026-08-29)

Companion to `s10-c2-network-transient-retry.md` / `s10-c2-t04a-measured-gate.md` / `s10-c2-t04b-truthful-apply-ux.md`.
Session `20260828_180654_be71b5`, worktree `s08-integration`, route `custom/meta` (Meta-max after C2-v2 override 00:30).

## 1. Wrapper EXIT=1 hang (T04C-C1 attempt1 03:48)

```bash
$ ls -la output/s10/c2/t04c-c1/dispatch-meta.log
-rw-r--r-- 1 Admin ... 7 Aug 29 03:48
$ cat output/s10/c2/t04c-c1/dispatch-meta.log
EXIT=1
$ wc -c output/s10/c2/t04c-c1/dispatch-meta.log
7
```

No RULES_LOADED, no TARGET, no inner `hermes --resume ...` output — the
CommandCode layer exited before the worker flushed anything. Compare:

- **Network transient** T03 R1/R2: 90 B `CommandCode error: {"type":"server_error","message":"Network connection lost."}` + wrapper EXIT=0.
- **This hang** T04C: 7 B `EXIT=1\n` only — different tail, same root: infrastructure hang, not product verdict.

**Manager action**: do NOT record BLOCKED_WITH_FINDINGS. Append registry
`wrapper EXIT=1 with 7B log (no worker output flushed; likely CommandCode
write hang) — not a product verdict; retrying same owner`, then:

```bash
HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume 20260828_023122_76b87e \
  -z "$(cat output/s10/c2/t04c-c1/prompt.txt)" --provider custom -m meta --yolo \
  >> output/s10/c2/t04c-c1/dispatch-meta-r2.log 2>&1; echo "EXIT=$?" >> output/s10/c2/t04c-c1/dispatch-meta-r2.log
```

If r2 itself is empty (T04C `dispatch-meta-r2.log` 0 B at 03:57), the
wrapper hang may persist — Manager may close by verifying **prior evidence
already suffices**: `output/s10/c2/j1..j5` ×2 logs, `output/s10/r1/run*`
artifacts, `output/s10/_build/frontend-build-manifest.json` trace.
Evidence migration pattern (03:56):

- `output/s10/r1/run1/**` (runtime/artifacts + motionforge.db) →
  `output/s10/c2/t04c-c1/run1-migrated-from-r1/`
- `output/s10/r1/run2/**` →
  `output/s10/c2/t04c-c1/run2-migrated-from-r1/`
- Companion `output/s10/c2/t04c-c1/evidence.json` with
  `{BUILD_ID, HEAD, route, preserved r1 ref, X01-X06 + measured gate unchanged}`
- Registry entry `T04C-C1 MANAGER CLOSURE` instead of worker J-gate;
  leave STATUS: TASK_SUBMITTED (no APPROVED/CLOSED).

Wrapper hang is a **retry** class, not a **blocker** class. Two consecutive
hangs still do not license a terminal BLOCKED_WITH_FINDINGS before the
evidence check.

## 2. Iteration-limit report-only resumption (T03 R4 / T04A R3 / T04B R2)

All three tasks hit the same shape in C2: code + pytest ×2 already PASS, but
the worker consumed all tool iterations before writing `TASK.md`/`LOG.md`/
`REPORT.md` and `output/s10/c2/**`.

Evidence per task:

| Task | Code + tests PASS | Missing at limit |
|------|-------------------|-----------------|
| T03-C2 R3 | 9/9 ×2 (49.28s/49.44s), .bin 0, Ruff 0 F* | LOG/REPORT + output/s10/c2/t03-c2/pytest_run*.log |
| T04A-C2 R2 | 40/41 → patch logical_id 41/41 | TASK/LOG/REPORT + output/s10/c2/t04a-c2/** |
| T04B-C1-R1 pre-val | gen-1/shot_a/mesh_warp 0 | TASK/LOG/REPORT + tsc/eslint/build/playwright/pytest logs |

Manager resume prompt for this shape (same owner, same route, no code edit):

> Tiếp tục đúng owner `…`. Code đã 9×2 PASS (see dispatch-meta-r3.log), thiếu
> khâu cuối: append LOG.md + REPORT.md với file:line trước/sau, provenance,
> verbatim pytest x2 commands, và output/s10/c2/** (pytest_run1/2.log,
> ruff_F.log, git_diff_check.log, git_status.log). Không sửa production.
> Xong ghi STATUS: TASK_SUBMITTED.

Verified J3/J4/J5 closures after report-only resumes:

- J3: `python -m pytest tests/test_s10_partial_recompute.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=...` → 9 passed 49.39s + 49.26s.
- J4: `tests/test_s10_structural_compare.py` → 41 passed 13.61s + 13.70s.
- J5: `tests/test_s10_full_apply_api.py tests/test_s10_full_apply_workflow.py` → 23 passed 62.29s + 61.48s.

Rule: do NOT treat a `TASK_SUBMITTED` that still reports "chưa xong, remaining
steps …" as terminal. The registry line stays `R(n) report pending — resuming
same owner to finalize`, never `DONE`.

## 3. Fresh-basetemp Manager gates (the independent re-verify)

Every J-gate re-runs the decisive suite(s) itself on **two fresh basetemp
dirs** with `MOTIONFORGE_DATABASE_URL=""` (UNSET) — never trusts the worker
log alone. T03/T04A/T04B J-gates above each ran `pytest -q -p no:cacheprovider
--override-ini="addopts=" --basetemp=C:/Users/.../s10c2-j{N}` and pinned the
`*.log` to `output/s10/c2/j{N}/`. A gate is MANAGER_VERIFIED only after
**your own** 2× PASS, not after the worker's.

Also: watch the payload parser. Two follow-up textual messages coined by
`responses_api` that contain no user action line will raise `hermes session
resume requires userPrompt` — use `-z PROMPT` with a real prompt body, never
an empty resume attempt. The 20:24 T02 R1b stall-recovery round hit exactly
this when two prior turns were pure registry appends + socket probes.
