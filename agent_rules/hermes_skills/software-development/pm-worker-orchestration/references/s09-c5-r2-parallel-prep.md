# S09-C5-R2 parallel PREP — maximum-safe concurrent fix wave (2026-08-27 revision C5-R2, 371-line prompt)

Authority: `docs/pm/prompts/S09_C5_FINAL_CORRECTION_MANAGER_2026-08-27.md` **Revision C5-R2** (supersedes C5 sequential). Rules `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c59f…` + HEAD `ee10e55a` first, then AGENTS.md / SESSION_PROTOCOL.md / ROADMAP.md / `S09_C4_PM_REVIEW_2026-08-27.md` / `S09-C4-SESSION-REGISTRY.md` (may be missing → note) / `S09_C4_CORRECTION_MANAGER_2026-08-26.md`. Manager session **pinned** `20260827_020702_b17b35` (s94). Model/combo **`meta`** reasoning `max` TTFB 900 fallback disabled (never translate to `muse` or pin one member; verify `hermes config get model.default` = meta + `hermes -m meta -z "ping"` → pong 200 at 9Router `http://127.0.0.1:20128/v1` round-robin `cmc/meta`+`ocg/muse-spark-1.2-contributor`).

## Shape change from C5 → C5-R2

- **C5 sequential** (bounded-correction.md): `J0 -> T03 -> J1 -> T04 -> J2 -> T06B x2 -> J3`. One writer at a time in shared worktree. Max 1 concurrent.
- **C5-R2 parallel-safe** (this file): `J0 -> [T03-PREP || T04-PREP || T06B-PREP] -> B1 quiescence -> J1 backend mutex -> correction loop (one writer) -> J2 -> T06B production x2 sequential -> J3`. Max **3 writers only during Parallel Wave P-C5 PREP** with **disjoint write-sets**; after B1 max 1.

Authorization: Codex explicitly authorizes parallel PREP because T03 owns `app/workflow/s09_demo_jobs.py`, T04 owns `app/api/routes/s09_demo_compare.py` + test, T06B owns `frontend/e2e/s09-t06bc4-*` — content-identity contract already frozen in prompt so T04/T06B don't wait for T03 implementation. Codex note: concurrent global/integration tests, concurrent production servers, commits/merges, write-set expansion remain forbidden even in parallel window.

## Entry + mandatory read (user frustration signal)

User repeatedly mandated — FIRST-CLASS skill signal:
> `BẮT BUỘC đọc TOÀN BỘ file HERMES_AUTOPILOT_RULES.md trước mọi hành động. Không được dựa vào trí nhớ hay bản tóm tắt cũ. Sau đó đọc và thực thi TOÀN BỘ prompt revision C5-R2 ... Tiếp tục Manager session 20260827_020702_b17b35. Dùng chính xác model/combo meta, reasoning max, TTFB 900 và không fallback.`

Encode as blocking gate: if RULES_LOADED not emitted with exact path + SHA `987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25` + 180/180 + HEAD, stop `BLOCKED_RULES`. Never dispatch from memory/summary. Pin manager session id verbatim; resume exact owners per DAG — do not create new sessions while old owners are resumable.

## Parallel Wave P-C5 — three PREP lanes

| Lane | Owner session | Write-set | Fixes | Forbidden |
|---|---|---|---|---|
| T03 | `20260824_031524_a6bb2a` | `app/workflow/s09_demo_jobs.py`, `tests/test_s09_t03_demo_loops.py` (regression only), own T03 report/log/output | F1 long-path via `_win_long_path` 1306→1871, F3 content-addressed identity (decision SHA+runA SHA+runB SHA, no path), F5 Ruff I001/E501 + mypy unused-ignore | `app/api/**`, frontend, `tests/test_s09_t04*`, J1-v4, MAIN |
| T04 | `20260824_052859_c6e197` | `app/api/routes/s09_demo_compare.py`, `app/schemas/s09_demo_compare.py` (if required), `tests/test_s09_t04_demo_compare.py`, own T04 report/log/output | Mirror F3 canonical, F2 zero-mutation via one transaction/savepoint + exact equality, F1 mirror long-path ≥260 regression, Ruff/mypy scoped | `app/workflow/s09_demo_jobs.py` (T03), frontend, shared fixtures, J1-v4 |
| T06B | `20260824_131423_423e42` | `frontend/e2e/s09-t06bc4-targeted-regeneration.spec.ts` + existing Playwright config if required + launcher helper under frontend E2E scope, own T06B report/log/output | F3 genuinely different verified content vs same-bytes-same-ID, F4 deterministic Windows launcher (no generic `bash` via WSL) + isolated runtime root/DB/output/ports + captured logs + `finally` cleanup | `app/**`, backend tests/fixtures, T03/T04/T05A/T05B, J1-v4 |

Parallel constraints (prompt §2): each worker gets unique temp/cache/DB/port; T06B must NOT start backend/Next or Chromium yet; no worker runs global/combined S09 gate; manager monitors write-set violations and stops only offending lane; workers exit `TASK_SUBMITTED` phase `PREP / AWAITING_B1_JOIN` — not final verification.

## Barrier B1-C5 — mandatory quiescence

Before any authoritative integration gate:
1. Confirm all three PREP processes exited.
2. Snapshot changed paths/hashes/mtimes; compare each to exclusive write-set — stop on collision, route to Codex.
3. Re-hash J1-v4 13/13 and confirm DB/test isolation.

## Join J1-C5 → J3-C5 — mutex gates

- **J1 backend mutex**: zero active writer, run T03+T04 focused suites + Ruff/mypy fresh, combined T03/T04 surface **x2** with separate long `--basetemp` ≥260. Persist commands/exit/durations/logs in new C5 evidence paths. If both fail resume T03 first then T04; if one fails resume only that owner. Repeat B1/J1 after every correction; no concurrent writers post-PREP.
- **J2**: after J1 green, re-hash 13/13, run TSC + scoped ESLint on stable tree, audit T06B PREP scope. Only then resume T06B exact owner for final Chromium **x2 sequential** with isolated resources; no backend writer may be active.
- **J3 final sprint gate** (after all writers exited, tree stable): 13/13 re-hash, focused T03/T04/T05/T06 + full S09 regression, Ruff/mypy over changed Python files, TSC/scoped ESLint/build, Alembic one head + upgrade proof, OpenAPI/route + target-profile invariants, Chromium x2 with evidence, `git diff --check` + write-set audit + dirty explanation, reconciled registry (no `PENDING`, exact status/session/files/commands/exit/evidence), positively attributed QA cleanup (never kill unrelated user processes). Any red gate → route to exact owner, repeat relevant join. Do not alter tests/scripts/fixtures from manager shell to turn gate green.

## Liveness + continuous execution (user: "chạy đi sao m cứ tự dừng xsuoost thế")

Prompt §5 + Rules §7: no blind sleep/570s loops; **bounded waits + poll**; 8 min no material progress → one concise continuation with exact remaining acceptance item; 20 min no progress → inspect process/session and recover same exact owner (no duplicate writers); transient provider failure → bounded 5-min backoff same session+model `meta`, record error; heartbeat ≤20 min while any lane active (user S09-C5 expects 20' + instant on exit/blocker; do not retain C4-META 30' for this wave). Max 3 only in P-C5, max 1 after B1; never concurrent production services/global gates.

User go-command `chạy đi` + ETA `estimate bao gio xong` arriving together → answer BOTH in same first reply: dispatch confirmation + status + concrete ETA table immediately (date first, never invent timestamps). Continuous `monitor -> review -> correction/resume -> verify -> report` to authorized terminal; do not stop because one worker replied or a join is pending.

## Terminal conditions

- Success only after every J3 item evidenced: `S09-C5 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`
- Failure: `S09-C5 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`
- Never write `APPROVED`/`CLOSED`/`SPRINT_COMPLETE`, open S10/S11/S13, commit/merge/push. Stop and wait for Codex re-review. Final response must include terminal, reconciled owner table, branch/HEAD/tree, J1-v4 13/13 proof, exact gates/results, evidence paths, process/port cleanup proof, residual risk.

## Prompt-file dispatch pitfall (verified 27/08)

Bash heredoc `cat > prompt.txt << 'PROMPT'` with quotes/apostrophes dies `unexpected EOF while looking for matching ''` (exit 2, worker never receives prompt — seen 11:38 T04/T06B dispatch). Fix: write prompts via `write_file` tool or Python file write, never bash heredoc for prompt bodies. Dispatch via `write_file` then `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner> -z "$(cat .../prompt.txt)" -m meta --yolo` with `background=true, notify_on_complete=true, workdir=s08-integration`. Verify `↻ Resumed session <id>` in dispatch log before treating lane as started.
