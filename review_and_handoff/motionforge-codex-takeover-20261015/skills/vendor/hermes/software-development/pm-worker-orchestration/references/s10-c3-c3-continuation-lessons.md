# S10-C3 Continuation Lessons — Dispatch Quoting, Segment-Motion Integrity, and Mypy Ownership Carry-Forward (2026-08-29)

Verified on worktree `s08-integration` HEAD `d3f6f79`, route `--provider custom -m meta` (Meta-max), DAG `T03-C3 -> J1 -> T04A-C3 -> J2 -> T01C-C5-static -> J3 -> T04C-C2 -> EXIT` under `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c5`.

## 1. Dispatch quoting trap — use prompt files, never inline `-z` with quotes

`hermes --resume <id> -z "Tiêp tục ... \"quotes\""` died `bash: unexpected EOF while looking for matching '"'` (proc_57e36e9671bb EXIT 2, T04A-C3 R3) because the outer `hermes --resume ... -z "$(cat prompt.txt)"` is already inside `bash -c` via `terminal()` and nested `"` break bash heredoc parsing. Fix is already in SKILL.md §1 (write `output/<lane>/prompt*.txt` then `-z "$(cat ...)"`) but THIS session proved the failure still happens when a manager writes a multi-line resume string inline with `"` instead of via file — the whole worker receives zero bytes and wrapper exits 2 with no worker log. Rule: every resume prompt, even short follow-ups, MUST be `write_file` then `cat`-sourced; never inline `-z "multi-line"` with quotes. T04A-C3 R3 was recovered by writing `output/s10/c3/t04a-c3/prompt-r3.txt` and retrying same owner — same prompt text succeeded.

## 2. `segment_motion` NOT NULL swallowed by `except: pass` → fail-closed BLOCKED

R2 for T04A-C3 reached 38/41 (three `CUT_FRAMES_MISSING + TRAJECTORY_MISSING` on `_seed_publication_directly` tests) despite correct `segments` derivation (`[50]` for 2 shots) and `JOIN occurrence_segment ON sm.occurrence_segment_id=os.id WHERE sm.workspace_id=:ws AND os.video_item_id=:vid` (since `segment_motion` has no `video_item_id`). Debug prints showed `segment_motion INSERT` missing `transform_json` (NOT NULL) raised `sqlite3.IntegrityError` inside `except: pass:` — silently forcing `_has_motion=False` → `trajectory/scale/rotation/contact = None` → `BLOCKED`. Fix: `transform_json='{}'` + `point_track_flow_ref_json='{}'` (+ `provenance`) plus seed `workspace_id`, `object_relative` CHECK (not `translate`), `logical_id`/`reasons_json`, real FKs. Seeds must provide every NOT NULL column or the except swallows the real error and the gate appears as a product defect. After fix: 41/41 ×2 (13.41s+13.90s).

Invariant: when a DB insert sits inside a bare `except: pass`, a subsequent `BLOCKED` on `TRAJECTORY_MISSING` etc. is a schema-fill bug, not a structural-gate bug — grep the seed helper for NOT NULL columns before suspecting the route.

## 3. Nine-file mypy ownership carry-forward (T01C-C5-static)

`python -m mypy app/workflow/s10_full_apply_jobs.py app/services/s10_structural_compare.py app/services/s10_recompute.py app/services/s10_multi_role_apply.py app/services/s10_full_apply.py app/services/s10_chunk_plan.py app/schemas/s10_full_apply.py app/persistence/s10_full_apply.py app/api/routes/s10_full_apply.py --ignore-missing-imports` reported 83 errors in 5 files pre-fix, 72 of which were stale `type: ignore[unused-ignore]` on the three T01C-owned files (`s10_full_apply.py`, `s10_full_apply_jobs.py`, `s10_full_apply.py` route). T01C-C5-static stripped those 72, fixed real `Any = None  # type: ignore[no-redef]` fallbacks and `no-redef` narrowing on generic args, and left T01C own at 0 while reporting 11 carry-forward errors (T04A `s10_structural_compare.py` 7× `unused-ignore`, T03 `s10_recompute.py` 1× `unused-ignore` + 3× `type-arg` missing generics). J3 accepted T01C scope clean (`grep s10_full_apply` on mypy log = 0) with carry-forward to owning lanes — no blanket `unused-ignore` removal across files the lane doesn't own.

Rule: a static-cleanup lane must only touch its exclusive write-set; remaining mypy errors are routed to the file's owner with evidence, not hidden by weakening `mypy.ini` or adding blanket ignores. Manager J-gate verifies T01C own = 0 separately from full nine-file status and records carry-forward as `BLOCKED_SCOPE_EXPANSION` if auto-fix would cross ownership.

## 4. J-gate never trusts worker counts — carry-forward still needs re-run

Manager J3 re-ran `MOTIONFORGE_DATABASE_URL="" python -m pytest tests/test_s10_full_apply_api.py tests/test_s10_full_apply_workflow.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp="C:/.../Temp/s10c3-j3a/b"` ×2 (62.26s + 61.98s, 23 passed ×2) and grepped mypy output for `s10_full_apply` hits = 0 to prove T01C own green independently of the nine-file summary. Worker REPORT claimed `STATUS: TASK_SUBMITTED` after 13.41s/13.90s but Manager still re-ran before MANAGER_VERIFIED — same pattern as T03-C3 (13×2) and T04A-C3 (41×2).

## 5. Small process lesson — T01C/T03/T04A report truncation via heredoc

T01C R4 dispatch used `cat >> docs/.../REPORT.md <<'EOF'` with a JSON-heavy report containing `"` and `$` — the shell heredoc truncated mid-file and the registry append that followed patched a stale string. Verified fix for T04A and T01C was `write_file` for REPORT/LOG, not heredoc, when the body contains JSON/manifest SHAs. See also `references/vietnamese-eta-typo-and-report-truncation.md`.

All three fixes landed via same-owner resume, same route `custom/meta`, no MAIN/S11/S13/J1 drift, `git diff --check` 0, `git status` allowlist.
