# S10 W1 — ETA, Gateway 524, Dispatch & J1 Traps (verified 28/08 00:15–01:40)

Source: S10 Full Apply Sprint, W1 (T01A‖T01B) → J1 → T01C, worktree `s08-integration` HEAD `d3f6f79`.

## 1. User heartbeat & ETA contract
- **Heartbeat:** 30' cadence + instant on lane exit / blocker. Honour exactly — user said `heartbeat mỗi 30p để báo cáo kết quả cho tôi hoặc khi có task gì đó xong hoặc có vấn đề` (27/08). Do NOT retain earlier 5' cadence.
- **Go + ETA co-occurrence:** When user sends `chạy đi` (or any go-command) TOGETHER with `bao giờ xong` / `ETA`, answer BOTH in the SAME first reply: dispatch confirmations + date-anchored ETA wall table (`date` first, `+07` anchor, per-phase wall 60–90' except T04C 90–150' + exit 40–60'). Never defer ETA to next heartbeat.
- **Silence trigger:** If no visible message for ~20–30', user asks `sao thấy dừng rồi?` / `sao lại dừng`. Proactive heartbeat must state which wait is legitimate: `RUNNING (workers)`, `waiting on J1 (T01A)`, or `parked at terminal awaiting Codex`. Never leave a gap without a stated wait reason.

## 2. Gateway 524 → RUNNING_RETRY_WAIT
- T01A dispatch 23:40 hit `524 Gateway request failed` (retryable). Per Rules §7: classify `RUNNING_RETRY_WAIT`, wait **5 min**, then `hermes --resume <same-session> -z "$(cat prompt.txt)" -m meta --yolo` with SAME prompt/TTFB/model. Never open new session. Loop indefinitely on 524/502.
- T01B continued RUNNING in parallel — retry-wait on one lane does NOT block disjoint lane.

## 3. Dispatch pitfalls (W1 verified)
- **Vietnamese heredoc EOF break:** `cat > prompt.txt <<'EOF'` with Vietnamese `BẮT BUỘC`, `—`, quotes breaks bash `unexpected EOF while looking for matching '''`. Fix: write prompt via `write_file` / Python `Path.write_text` (or `execute_code`), never shell heredoc for Vietnamese prompts. Verified: T01A/B first heredoc failed, file-write rewrite fixed (45/37 lines).
- **Shell `&` blocked:** `terminal` foreground rejects `&` (`Foreground command uses '&' backgrounding`). Fix: use `terminal(background=true)` one process per lane, `notify_on_complete=true`.
- **Prompt flag:** Installed `hermes` uses `-z` (not `-q`). Verify via `hermes --help` before launch — old packet note `-q` caused EXIT=2 wave in S09-C4.

## 4. J1 gate verification traps
- **Alembic CWD trap:** `alembic.ini` has `script_location = migrations` (relative). Running from MAIN (`C:/Users/Admin/MotionForge2D`, 4 migrations) returns `d5e6f7a8b9c0 (head)` hiding 13 worktree-only revisions. Must `cd s08-integration` before `alembic heads/history/current/upgrade` to see `a10b11c12d3e (head)` + 17-file chain. Verify via `ScriptDirectory.from_config` if unsure.
- **Pytest invocation trap:** `pyproject.toml` addopts breaks `pytest --cache-clear` (`unrecognized arguments: --cache-clear`). Correct isolated form: `pytest <tests> -v -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>` . Use for every ×2 gate, record basetemp in registry.
- **J1 close criteria:** 47 passed ×2 (21 domain+6 migration + 26 planner) on distinct basetemp, `alembic heads` from worktree, `ruff` scoped (E501 P2 on long SQL literals allowed), `mypy --strict` clean, `git diff --check 0`, `git status` only allowlist. Never derive PASS from worker stdout alone — re-run yourself.

## 5. T01B planner purity contract (reference for future pure services)
- No DB/IO/time/process/path; hash only from pinned canonical JSON (`sort_keys`, `separators`); deterministic IDs via `sha256(pinned_hash+position)`; overlap = context-only metadata; fail-closed on malformed manifests. 26 tests ×2 is the purity proof pattern.
