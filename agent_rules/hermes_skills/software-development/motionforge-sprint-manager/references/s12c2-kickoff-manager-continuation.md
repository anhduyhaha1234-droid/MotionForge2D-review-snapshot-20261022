# S12-C2 kickoff — manager continuation, role corrections, route override (2026-09-09)

Pattern for a **correction-sprint continuation in the SAME manager session** when the
Codex review ships a fresh bounded prompt (S12-C2-HERMES-PROMPT.md) and the user pastes it
into the already-running manager chat ("Tiếp tục S12-C2 trong đúng manager <sid>").

## 1. Identity: continuation, NOT a new manager
- Prompt §1 pins the manager by SID — the chat it lands in must equal that SID
  (`hermes sessions list` top row; here `20260908_141259_24fac4` = s12-3).
- Old manager `20260905_162953_5a5cda` is ABSENT from state DB — do not resume/impersonate it.
- Old preflight session `20260908_011327_cc3b74` is not the dispatch source.
- Dedicated INT01 `20260908_013539_7b0a4f` EXISTS and last reported INT01_READY_W4 —
  Git transport belongs to it; the Manager's own direct commit+push of `ea78497` (C1 packet)
  is a recorded role-crossing (review F11) — stop Manager Git writes in C2.

## 2. Required reading before dispatch (same turn)
- FULL rules (RULES_LOADED + line count), review dir
  `.../outputs/s12-c1-review-20260909/`: REVIEW.md (F01–F11 + R01–R13 mapping), MATRIX.md,
  micro/persistence/worker-r2 results, owner-audit.json, process-snapshot.json, commands.jsonl.
- Canonical pin: HEAD `ea784974…` = product `60d58641…` + C1-packet-only commit. Verify
  local==remote + porcelain 0 BEFORE dispatch.

## 3. Watcher stop: stale review PIDs are NOT the live PIDs
- process-snapshot.json lists reviewer-observed PIDs (39444/38596/21496) — hours later the
  live loop has NEW PIDs (69222 parent bash + 69234 child, same cmdline
  `watch_24.sh` under the C1 evidence root, created 21:47:41). Attribute by FULL cmdline +
  creation time, kill the live PIDs, `ps`-prove empty. Never blind-kill the stale numbers,
  never pkill/killall python.

## 4. Model policy: prompt pin vs live quota vs live user order
- Prompt §2 pins CMC (`cmc/meta/muse-spark-1.3-contributor` @ muse, max, fallback OFF),
  superseding older MODEL_SWITCH.md to ocgfree; historical ocgfree T06B-fix attribution stays.
- PROBE before dispatch (`hermes chat -q "Reply EXACTLY: MODEL_PROBE_OK" -m <model>`):
  CMC returned 429 weekly-quota with reset timestamp `2026-09-11T17:23Z` — that is a
  determinate BLOCKER, not a retry-loop (Rules §7 5-min retry does not apply).
- User then ordered (live chat, latest-wins): "đổi hết worker sang ocg/deepseek-v4-flash đi"
  → ALL C2 workers + INT01 resume use `ocg/deepseek-v4-flash` @ provider `custom` (9Router),
  reasoning max, fallback OFF. Verify the ID EXISTS via full-list JSON match (149 models).
- Record old→new + reason in `<C2-root>/MODEL_SWITCH.md`; never rewrite history; never pick a
  route silently when a prompt pins another — user order is the only override.

## 5. C2 evidence root + guard before dispatch
- One fresh root `<UTC-run-id>-C2` (here `20260909-124300-C2`), never reused; write
  STATE_RECONCILIATION.md (identity/canonical/watcher/owner table/model) + BLOCKER_LOG.md.
- Byte-guard the W1 writable set (schemas/preflight/route/contract/app.py S12 registration)
  with SHA256/bytes/lines before dispatch.
- Dispatch W1 in the SAME turn once preflight passes (prompt §1 bans plan-only replies):
  `cd <task-worktree> && hermes chat -q "$(cat <C2-root>/s12-t01/prompt.md)" -r <exact-owner-sid>
  -m ocg/deepseek-v4-flash --provider custom -Q` bg + notify_on_complete.
- W1 T01 packet must bind the C2 findings (F02 server-owned authority, real Job ID, zero-mutation
  invalid cases) + C2 matrix rows C02/C03/C04 + explicit model/route override note.

## 6. C2 anti-substitution reminders (from review F01–F11)
- C06: tamper frame_count (not plan_hash); C08: stale ORM transition contention; C10: product
  runner 4K (not standalone FFmpeg 4K fixture); C13: byte-changed chunk MUST be rejected;
  C14/G: kill the OWNED job process, same DB, fresh PID; C22: valid result MUST play/download
  (C1 asserted the opposite — reversed acceptance); full S12 collection must collect together
  (per-dir totals do not repair the duplicate-basename collection failure — see
  s12c1-int01-merged-gate-and-route-quota.md for the per-dir gate loop).
