---
name: pm-worker-orchestration
description: Use when running PM-gated worker sprints and freeze gates.
---

# PM Worker Orchestration — dispatch, verify, gate

You are the Manager in a PM-gated sprint: workers write all production code;
you preflight, dispatch/resume exact owner sessions, hold exclusive write-set
locks, verify evidence by running commands yourself, and pin join-gate freezes.
Never write production code/tests/fixtures yourself; never trust a worker
report without re-running the decisive command.

> Manager detail bank (curated references):
> `references/s11-isolated-worktree-full-sprint-playbook.md`; `references/parallel-verify-and-prestage.md`; `references/t03-required-reading-death-pivot.md`
> `references/model-route-inheritance-and-mid-sprint-switch.md`; `references/s11c1-watchdog-terminal-marker-design.md`
> `references/gate-calibration-and-prevalidation.md`; `references/hermes-cli-worker-dispatch-and-owner-transfer.md`
> Full annotations for every reference: `references/detail-bank-index.md`.
> `references/byte-exact-patching-crlf-escaping-and-truncation.md` + `templates/byte-exact-patch-runner.py` — CRLF/escape/truncation-safe bounded patching of live harness files (open('w') truncates before errors — tmp+os.replace; chr() escape sentinels; count==1 anchors; post-verify hash/bytes/lines).
> `references/structured-terminal-records-and-consumer-patching.md` — structured terminal JSON per invocation bound to the immutable dispatch row; fail-closed reconciliation; patch + test the ACTUAL dispatcher/heartbeat consumers in an isolated MF_RUN_ROOT scaffold (kills prose-token classifiers).
> `references/controller-lock-gpu-lease-and-windows-process-identity.md` — filelock one-controller; GPU lease that survives detached children; psutil identity (pid+create_time, AccessDenied=UNKNOWN); venv-python two-process shim; STOP-file monitor shutdown with census.
> `references/session-db-controller-reconciliation.md` — identify the CURRENT manager session and the ACTUAL controller from the read-only Hermes state.db (messages.timestamp, prompt-marker search, registered-vs-actual discrepancy, zero-writer proof legs).
> `references/worker-ack-without-commit-and-verifier-gaps.md` — worker ack-without-
> commit, zero-byte TASK_SUBMITTED, $TEMP hijack, per-dir pytest (duplicate test
> basenames), watchdog edit-vs-running-process, model quota fallback.
> `references/correction-round-immutable-evidence.md` — per-round immutable
> before/after evidence roots (P2 evidence-integrity), RED-first contract-repro
> pattern with JSON sidecar-before-asserts, path-depth-tolerant repo-root
> discovery, per-round exact model probe, heartbeat cron script location.
> `references/prep-review-reproduction.md` — PREP-phase reproduction of
> independent-review findings (real route + real JobService + isolated SQLite:
> importlib test-module reuse, real-service reuse vs second-DB trap, job_type
> column, truth-semantics record-don't-assert).
> (`schedule='10m'` is ONE-SHOT — use cron `*/10 * * * *` + `repeat=N` +
> `deliver='origin'`; a fired one-shot vanishes so `update` fails — list first;
> model-less crons silently inherit `model.default` — override per-job via
> `hermes cron edit --model --provider`, user model overrides apply to crons too).
> NEW (2026-08-31, S10-C6A): see `references/acceptance-integrity-and-resume.md`
> for iteration-cap resume contracts, foreign-owner failure attribution, E2E
> acceptance-theater detection, the client-fabricated-authority anti-pattern
> (server-derived v2 fix), owned-process cleanup with launch-record proof,
> baked-origin port coupling, the broad-except cancel-route lock-swallow P0,
> fast-run E2E race classification, and seed-asset UUID naming traps.
> NEW (2026-08-31, S10-C6B): `references/model-route-override-probe.md` — model-override probe protocol, case-sensitive ids, `data: [DONE]` trap, BLOCKED_MODEL_ROUTE.
> NEW (2026-09-02, S10-C6G C14): `references/forensic-recovery-incident-orchestration.md` — exact-hash test-authority recovery: PREP bundle, owner-ledger correction, resume gate.

## Dispatch mechanics (Windows + hermes CLI)

1. ALWAYS write the worker prompt to `output/<lane>/prompt.txt` and dispatch
   with `-z "$(cat .../prompt.txt)"`. Inline printf prompts with quotes die on
   bash EOF errors and the worker silently receives nothing.
   HUGE PROMPTS: a `write_file` for a >8K-token prompt can stream-timeout and
   the prompt file never lands. Write the prompt as TWO files (`prompt.txt` +
   `prompt_part2.txt`, each small) and dispatch with
   `-z "$(cat prompt.txt; echo; cat prompt_part2.txt)"` — identical launch form
   to the single-file case, no timeout.
   TRUNCATED DISPATCH LOG: when a worker hits its tool-call iteration cap, the
   dispatch log often ends MID-REPORT (partially flushed, e.g. a 4-line r2 log
   after a full r1). Do NOT conclude from a truncated tail. Audit DISK truth:
   evidence dirs mtimes, `e2e-results/.last-run.json`, `env.json` BUILD_ID,
   driver logs, DB probes. Also: processes the WORKER spawned (backend uvicorn,
   playwright) are NOT in the Manager's process registry — poll them by port
   (`netstat -ano`) and exact command line, and find ownership in the worker's
   dispatch logs (e.g. "probe trên 8399 đã kill" claims vs. a live listener).
   Cleanup proof = command line + port + launch-record reference, then kill the
   exact PID only (never pkill/killall python). VERIFY the prompt
   flag against the INSTALLED CLI before launching (`hermes --help`: one-shot
   prompt is `[-z PROMPT]`; older packets/notes said `-q`, which this build
   does NOT accept as prompt input) — C4 Wave A launched all 5 lanes with `-q`,
   argparse consumed the whole prompt text as the COMMAND name and every lane
   died EXIT=2 with a usage dump before any worker saw a byte of the task.
   After EVERY launch confirm BOTH (a) no argparse/usage error in the log head
   AND (b) the `↻ Resumed session <id>` line lands in dispatch.log within the
   startup window (~2 min) before treating the lane as started — an exit-2
   wrapper leaves no worker-side trace at all, and a missing resume line means
   the lane never actually began despite a live process. When unsure which
 invocation a prior round used, read THAT round's dispatch.log head plus
 `hermes --help`; never trust stale notes or memory for CLI syntax.
 PowerShell quoting: single-quote the whole `powershell -NoProfile -Command
 '...'` payload so bash does not expand `$_`/`@{}`; double quotes inside get
 eaten and inline bash comments leak into the PS parser (parse-error garbage).
 Never pipe `hermes --resume …` through `| head -n 200` or any truncating
 pipe — head closes after 200 lines and hermes dies with SIGPIPE/broken pipe,
 killing the worker mid-prefill (S09-C4 26/08: first T04 Muse dispatch used
 `… --yolo 2>&1 | head -n 200`, stalled at 5 lines/2.0K for 50+ min with zero
 progress until killed and relaunched with `>> dispatch.log 2>&1` instead;
 always redirect to a log file, never through head/tail).
2. Resume corrections against the EXACT owner session id; new task = new
   session. Keep provider/model/API mode identical every resume.
3. Background-dispatch each worker (`terminal background=true,
   notify_on_complete=true`), one process per lane, max parallel = what the
   prompt authorizes (typically 5). Track proc ids in your registry.
4. Liveness = log-size delta + the `↻ Resumed session` line + EXIT marker
   inside dispatch.log, cross-checked with process liveness (PID + CPU probe)
   when the log stays flat — a live process with a never-growing log is
   exactly the router-stall / compression-silence case below, and killing on
   log silence alone would murder healthy lanes. Workers exit early mid-gates
   routinely (EXIT=0 with ruff/mypy leftovers): root-cause from disk evidence
   yourself, then resume owner with a fix packet naming the finding precisely.
5. Version-constant bumps are a class of incomplete work: when a worker bumps
   any SCHEMA_VERSION-style constant, audit the paired fixtures/JSONs for the
   old value yourself (grep both sides) before accepting the lane — one round
   shipped script=3 vs fixture=2 and 8/29 tests failed fail-closed on it.
6. STALLED WORKER ≠ DEAD WORKER (API-streaming hang signature): log size
   frozen 15+ min, process chain alive, but the leaf python's CPU increments
   only hundredths of a second per minute (+0.05–0.16s measured across a
   5-minute window on a real hang) — a busy worker burns whole seconds of CPU
   between checks. Diagnose with TWO probes ~60–90s apart: identical log
   byte-size twice, THEN leaf CPU via powershell `Get-Process -Id <pid>`
   around a sleep. Find the leaf by walking the tree: wrapper bash PID →
   `Get-CimInstance Win32_Process -Filter 'ParentProcessId=<pid>'` →
   hermes.exe → python.exe. Recovery per Rules §7: kill ONLY those exact
   PIDs, WAIT the full 5 minutes, resume the SAME owner session with the
   SAME prompt file/provider/model — session context survives the kill, so
   mid-flight edits carry into R2 (T04-C3 binding R1→R2 recovered exactly
   this way without losing a diff already written to the log). Never launch
   a fresh session for a stall; never declare BLOCKED_LIVENESS on a
   live-but-idle chain.
   TWO lookalikes to rule out BEFORE killing:
   - POST-RESUME COMPRESSION SILENCE: a freshly-resumed LONG owner session
     (hundreds of messages) can sit with ZERO log output for 5–10 minutes
     while Hermes loads/compacts context — leaf python CPU creeps upward
     slowly (+0.05–0.65s/min) and then the log bursts tens of KB at once
     (T04-C3 R2: frozen at 404106 B for ~9 min after relaunch, then
     +14.9KB in one step and normal operation). Silence that begins
     IMMEDIATELY after a resume of a big session = wait longer; silence
     that begins AFTER visible mid-work progress (log grew, edits landed,
     then froze) = the real stall signature above.
   - RECOVERY-KILL EXIT CODES: after YOU kill a stalled wrapper, the
     pending echo writes `EXIT-<tag>=127` (bash killed, not a worker
     verdict). Record 127 as "recovered by Manager", never as a worker
     failure — and never let a later reader mistake it for the lane's own
     result.
   - ROUTER-WIDE TTFB STALL (26/08 C4, verified): ALL lanes (plus the
     Manager chat itself) sit at zero log output with ESTABLISHED sockets to
     the router; `hermes/logs/agent.log` shows repeating "Codex stream
     produced no bytes within TTFB cutoff (120s > 120s)" + internal retry
     lines. This is a PROVIDER outage shape, not dead workers and not the
     per-worker streaming hang: do NOT kill anything, classify every lane
     `RUNNING_RETRY_WAIT` per Rules §7, keep 8-minute audit cycles, and say
     plainly in the heartbeat that the router is the blocker. Distinguisher:
     per-worker hang = ONE lane frozen while others progress; router stall =
     EVERY lane silent simultaneously including your own session.
   - MUSE VIA 9ROUTER MODEL ROUTING (S09-C4 Muse, verified 26/08): this
     project's Muse workers use `provider: muse` at
     `http://127.0.0.1:20128/v1` with `model: ocg/muse-spark-1.2-contributor`,
     `api_mode: codex_responses`, `reasoning: max`, `fallback: disabled`
     (config.yaml shows `model.default: ocg/muse-spark-1.2-contributor` /
     `provider: muse`). Raw `curl -H \"Authorization: Bearer $API_KEY\"` to
     `127.0.0.1:20128/v1` ALWAYS returns `Missing API key` even with the
     config key — Hermes injects the credential via its egress
     credential_pool (`custom:meta-muse-via-9router` / `custom:9router`,
     secret_fingerprint `sha256:3848af8f...`) so the probe MUST be
     `hermes -z \"ping\" --provider muse -m ocg/muse-spark-1.2-contributor`
     (HTTP 200 `pong` in ~0.05s via codex_responses), never a raw curl and
     never `POST /v1/chat/completions`. Large prompts (150k-token prefill)
     need `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900` or the router kills the
     stream at 120s before the first byte — S09-C3/C4 measured 47s for a
     16-token probe and 22 min of silence before the first log burst on a
     resumed 4000-msg session. Dispatch verbatim:
     `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner_id> -z \"$(cat prompt.txt)\" --provider muse -m ocg/muse-spark-1.2-contributor --yolo`
     from the worktree cwd; the 12-char hex suffix (`645cde` etc.) IS the
     owner session id — do NOT create a new session for a correction.
     `wire_extraction_segment` in C4 prompts is the repo's
     `create_extraction_segment` (`app/persistence/structural_evidence.py:1334`,
     requires `logical_id` + `segment_id` deterministic); `create_segment`
     (1185) OWNS `logical_id` via `_new_id()` and rejects caller values
     (C1-F2). Bypass `REQUIRED_JOB` guard by using
     `confidence_source=\"user\"` or `\"manual\"` with `source_job_id=None`
     — if it still demands a COMPLETED DISCOVER_OBJECTS job, return
     `BLOCKED_WITH_FINDINGS` with file:line, don't silently open T05A scope.
   - META COMBO ROUTING (S09-C4-META, verified 27/08): this cycle's workers
     use combo `meta` at `http://127.0.0.1:20128/v1` — `model: meta`
     (9Router `round-robin` `cmc/meta/muse-spark-1.2-contributor` +
     `ocg/muse-spark-1.2-contributor`), `reasoning: max`, fallback disabled,
     `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`. Probe `hermes -m meta -z "ping"`
     → pong 200. Dispatch `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes
     --resume <owner_id> -z "$(cat prompt.txt)" -m meta --yolo` or new
     `hermes -z "$(cat prompt.txt)" -m meta --yolo` from worktree cwd.
     Never translate `meta` to provider alias `muse`, never pin
     `ocg/muse-spark-1.2-contributor` directly, never use `alpha` or other
     models when the prompt mandates `meta`. Round-robin within the two
     members is intended combo routing; fallback outside the combo is a
     blocker.
   - DEEPSEEK V4 FLASH ROUTING OVERRIDE (S10-C2, verified 28/08, CORRECTED): model
     override `deepseek-v4-flash` (effective 9Router `ocg/deepseek-v4-flash`, reasoning
     max, fallback OFF, TTFB 900) MUST be dispatched with the FULL model id exactly as the
     manager chat session runs it: `--provider custom -m ocg/deepseek-v4-flash`. ALWAYS
     include the `ocg/` prefix — 9Router resolve the BARE string `deepseek-v4-flash`
     (even with `--provider custom`) through its `kv` table to `providerAlias: cmc` →
     OpenRouter upstream `[openrouter/deepseek-v4-flash]`, whose credits are a SEPARATE
     exhausted pool; the `ocg`-prefixed id resolves to `providerAlias: ocg` → opencode-go
     connections (several active keys, 1945 successful deepseek-v4-flash calls). The
     session-history user correction "dùng chính model tôi đang chat với bạn" is the rule:
     worker route = the exact provider+model pair of the manager chat. Also: bare
     `-m deepseek-v4-flash` with NO provider flag dies `No usable credentials found for
     provider 'deepseek'. Set DEEPSEEK_API_KEY.` — the string is treated as a provider
     name when unmatched. Probe BEFORE dispatch: `hermes --provider custom -m
     ocg/deepseek-v4-flash -z "ping" --yolo` → `pong`. Dispatch verbatim:
     `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner_id> -z
     "$(cat prompt.txt)" --provider custom -m ocg/deepseek-v4-flash --yolo`.
   - DEEPSEEK V4 FLASH ROUTING — C4 UPDATE (verified 29/08): the C4 prompt
     text literally demanded resume commands use `-m deepseek-v4-flash` and
     "không dùng --provider custom" — LIVE PROBE PROVED THE PROMPT LITERAL
     WRONG: bare `-m deepseek-v4-flash` dies `No usable credentials found
     for provider 'deepseek'. Set DEEPSEEK_API_KEY.` (there is NO provider
     named `deepseek` in this config), and `-m deepseek-v4-flash --provider
     custom` misroutes to `HTTP 404: No active credentials for provider:
     openrouter`. The working dispatch is the FULL config-matched id with NO
     provider flag: `hermes -z "ping" -m ocg/deepseek-v4-flash --yolo` →
     `pong ✅`, and `logs/agent.log` rows confirm `model=ocg/deepseek-v4-flash
     provider=custom`. So: never take a prompt's model string as ground truth
     — probe first; when a selector fails, read `~/AppData/Local/hermes/
     config.yaml` `providers.<name>.model` and probe the exact id that
     matches the effective model the prompt requires, then record the probe
     matrix (bare FAIL / full-id pong) in the registry as route evidence.
     Dispatch verbatim: `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes
     --resume <owner_id> -z "$(cat prompt.txt)" -m ocg/deepseek-v4-flash
     --yolo` (no `--provider` flag — Hermes resolves the provider whose
     `model:` equals the id). `hermes model` is an INTERACTIVE picker, not a
     list command; `hermes model list` errors — probe with `-z "ping"` is the
     only reliable route check.
   - META-MAX SAME-MODEL-AS-CHAT RULE (S10-C2, verified 28-29/08, user correction): when the user says "dùng chính model tôi đang chat với bạn" or "đổi worker sang model Meta-max giống bạn", worker route MUST be the exact provider+model pair of the manager chat session — never a bare model id, never an opencode-routed alias. Verified 9Router mapping 29/08: `ocg/deepseek-v4-flash` via `custom` → `providerAlias ocg → opencode-go` (pong, 1945 successes); bare `deepseek-v4-flash` via `custom` → `providerAlias cmc → OpenRouter` (HTTP 402 `in_flight_budget_exhausted` / `Prompt tokens limit exceeded 64350>58353`); `ocg/muse-spark-1.2-contributor` via `muse`/`opencode` → HTTP 404 `No active credentials for provider: opencode-go`; `meta` via `custom` → combo `meta` (`cmc/meta + ocg/muse-spark`) → pong — correct Meta-max dispatch is `--provider custom -m meta --yolo`. Before ANY worker dispatch probe the exact pair (`hermes --provider <p> -m <m> -z "ping" --yolo`); a tiny probe pong does NOT prove a 60k-token prefill will pass, but wrong-route 402 is deterministic. When user orders "bỏ hết các model khác khỏi luồng worker nhất là openrouter", treat as hard routing constraint: no `openrouter`/`cmc`/bare-id/fallback; record in `S10-SESSION_REGISTRY.md` as `USER MODEL OVERRIDE C2-vX: <provider/model>` with pong evidence.
   - OPENROUTER IN-FLIGHT BUDGET 402 CONTENTION (S10-C2, verified 28/08):
     when the Manager's own chat session runs the SAME model through the SAME
     9Router/OpenRouter upstream as the worker, every Manager tool-call is a
     ~200k-token in-flight request (agent.log rows: `model=ocg/deepseek-v4-flash
     provider=custom … in=215822 out=…`). A worker prefill on top of that
     exceeds OpenRouter's in-flight budget -> worker dies with `HTTP 402
     in_flight_budget_exhausted … Retry after in-flight requests settle`
     (the raw 402 appears in dispatch.log only at exit). BEFORE exit this can
     masquerade as (a) an early exit with a 156-byte log (worker printed one
     line then died) or (b) a 37-min zero-log "stall" with leaf CPU creep
     ~0.009s/min — the worker is waiting on in-flight settle, not a dead
     thread, and NOT the compression-silence signature (0.05-0.65s/min) nor
     a true stall. Decisive attribution: Manager+worker share model/upstream
     AND dispatch-log tail shows 402 after exit. POLICY FIX: dispatch ->
     append registry -> END THE TURN. NO manual polling loops (no repeated
     `process wait`/tail) while the worker runs — `notify_on_complete=true`
     wakes the Manager and the worker keeps the whole in-flight budget.
     After a 402: wait 5 minutes for settle, then resume the SAME owner
     session with the SAME prompt/model (Rules §7). Never classify this as a
     dead worker and never create a replacement session for it.
     See references/s10-c2-meta-max-same-model-routing.md for the S10-C2 Meta-max same-model-as-chat routing matrix (bare vs ocg/ prefix → cmc/OpenRouter 402 vs opencode-go, manager-chat identity, probe recipe).
     See references/s10-c2-t01c-meta-max-continuation.md for the 00:47 J2-verified continuation (Meta-max switch mid-DAG, same-owner resume, 23/23×2 + 23/23×2 independent gate).
     See references/s10-c2-deepseek-route-and-inflight-402.md.
   - COMMANDCODE NETWORK TRANSIENT (S10-C2 T03, verified 29/08): `CommandCode error: {\"type\":\"server_error\",\"message\":\"Network connection lost.\"}` is a transient infrastructure failure (dispatch-meta.log 90 B, wrapper EXIT=0, no worker output). Distinguish from 402 and from stall/compression: ping 1.1.1.1 0% loss + `hermes -z ping` pong + 9Router :20128 ESTABLISHED = upstream transient, not product failure. Rules §7: wait + retry same owner same provider/model (retry cadence), do not create new session, do not treat as BLOCKED_WITH_FINDINGS until 3× persists. Log as `T03-C2 R(n) network drop — ping OK, 9Router OK — retry same owner`.
     See references/s10-c2-network-transient-retry.md.
     See references/s10-c2-t03-report-finalization.md for the T03 report-finalization + J3×2 verified continuation (network 90B → 8096B gate, iteration-limit resumption, same-owner R4 report-only prompt, J3 9/9×2 49s, seed authority fix).
     See references/s10-c2-t04a-measured-gate.md for the T04A measured-gate continuation (server-derived metrics, shot_a/mirroring grep ZERO, direct seeding helper, z_order logical_id, J4 41/41×2).
See references/s10-c2-t04b-truthful-apply-ux.md for the T04B truthful Apply UX (fabricated removal gen-1/shot_a/mesh_warp, explicit checkpoint select, Vietnamese helper text 11px, empty body server-truth, J5 23/23×2 + TSC/ESLint/build).
   - WORKER RULES_LOADED / SELF-REPORTED PREFLIGHT CLAIMS ARE NOT EVIDENCE
     (S10-C2 R4, verified 28/08): a worker REPORT stated `RULES_LOADED SHA
     29ea6b60…, 37 dòng` while the real rules file is 180 lines, SHA
     987386c5… — fabricated/copy-pasted claim with no bearing on the actual
     tests. Do not fail the gate on such claims (gate on real test/disk
     evidence), but record them in the registry as report-inaccuracy items
     for Codex review; never repeat a worker's self-reported SHA as fact.

   - WRAPPER EXIT=1 NO-OUTPUT HANG (S10-C2 T04C, verified 29/08 03:48): `dispatch-meta.log` 7 B `"EXIT=1\n"` with no worker output flushed is a CommandCode write hang, not a product verdict. Distinguish from a real worker failure (which prints RULES_LOADED + TARGET + logs) and from network 90 B transient (`Network connection lost`). Probe: `wc -c dispatch-meta.log` == 7 and `cat` shows only EXIT line → retry SAME owner SAME prompt SAME `custom/meta` (Rules §7). If repeated, Manager may close by verifying prior evidence (J1-J5 + build manifests) and migrating `output/s10/r1/run*` evidence to `output/s10/c2/<lane>/run*-migrated-from-r1` + `evidence.json` — never treat wrapper hang as BLOCKED_WITH_FINDINGS.
   - ITERATION-LIMIT REPORT-ONLY RESUMPTION (S10-C2 T03 R4 / T04A R3 / T04B R2, verified 29/08): worker can land all code fixes and `pytest ×2 PASS` (9×2 / 41×2 / 23×2) but exhaust tool iterations before appending `TASK.md`/`LOG.md`/`REPORT.md` + `output/s10/c2/**` evidence. Next resume prompt must be report-only: "Code đã PASS (see dispatch-r3.log), chỉ còn append LOG+REPORT với file:line + provenance + verbatim pytest commands + STATUS: TASK_SUBMITTED, no code change expected" — same owner, same route. Manager J-gate must verify REPORT exists before MANAGER_VERIFIED.
   - ITERATION-CAP MID-VERIFY — RESUME WITH THE SAME PROMPT, NOT REPORT-ONLY (S10-C4 T01C-C6, verified 29/08): a DIFFERENT exhaustion shape: code edits all landed (sometimes with a last patch NOT yet re-run) but the worker hit the iteration cap INSIDE the final verify loop. The honest worker prints a status line explicitly saying `STATUS hiện tại: RUNNING (iteration cap giữa vòng verify)` + lists the exact remaining steps (rerun targeted ×2 fresh, ruff/mypy, sweeps, evidence, docs). This honest RUNNING claim is itself evidence of discipline — trust the phase distinction: code done + verify NOT done → resume with the SAME full prompt (or a continue packet restating its own remaining-steps list); code done + verify PASSED → report-only short prompt. Do NOT declare TASK_SUBMITTED from a worker that says RUNNING, and do NOT rewrite a fresh prompt — the worker's own context already carries the patch queue.
   - `Codex response remained incomplete after 3 continuation attempts` — CONTENTION/COMPLETION TRANSIENT with a 1-LINE LOG (S10-C4 T03-C4, verified 29/08): the dispatch log is exactly one line and nothing else flushed, yet the worker DID land real edits on disk before dying (check `ls -la --time-style=full-iso` mtimes of the lane's files — s10_recompute.py mtime moved 21:19→21:40). This is NOT the 7B `EXIT=1` write-hang and NOT the 90B network-lost: treat like Rules §7 transient — wait 5 minutes, `python -m py_compile` the touched file to prove it is not half-written, then resume SAME owner/session/prompt/model. Distinguisher from the write-hang is the mtime evidence of landed edits; never re-dispatch a fresh session based on the one line.
   - RESUME-IMMEDIATELY vs WAIT-5-MIN DECISION (S10-C4 T03-C4 R2→R3, verified 29/08): after a worker-REPORTED continuation request (honest RUNNING + "cần tiếp tục lượt mới" + remaining-steps list), resume IMMEDIATELY — no 5-min wait, that wait is only for transient infra failures (network lost, incomplete-response, 402 in-flight, wrapper hang). Check the report's failure diagnosis: if the worker says "đã chẩn đoán tận gốc + hướng xử lý tiếp" it is requesting work continuation; only infarct-class exits (no worker output at all) take the wait.
   - BANNED BYTE-TRICK ⇒ RESEED THE ASSERTING TEST, DON'T REUSE THE TRICK (S10-C4 T03-C4, verified 29/08): C4 forbids correction-ID hash perturb / generic byte-difference tricks for recompute. The C3-era test `test_c3_affected_adapter_invocation_and_evidence` then FAILED because the persisted mask region `[0.10,0.10,0.40,0.40]` now equals the base mapping region — the real SpriteAffineAdapter renders byte-identical media, so "affected bytes changed" can no longer pass. Lesson: when a correction round outlaws a deterministic-perturb trick, the tests that asserted "unequal SHA" MUST be reseeded with genuinely different persisted authority (e.g. correction region `[0.10,0.10,0.60,0.60]` vs base `[0.40,0.40]`) and should assert corrected visual/structural FACT + exact request identity, not merely `before != after` bytes. Probe first whether the real renderer actually changes output for the seeded authority delta — a RegionMapping anemic delta renders identical output and the failure is a seed problem, not a code problem.
   - LONG-PATH `\\\\?\\` PREFIX MISMATCH — ROOT-CONTAINMENT VARIANT (S10-C4 T01C-C6, verified 29/08): Windows >260 path tests fail with containment errors when `_win_long_path`/`\\\\?\\` is applied to OUTPUT paths only while the managed workspace root is NOT prefixed — checkers (e.g. `renderer_contract.py:542` containment) compare `output_media` against the unprefixed `workspace_root` and fail even though both refer to the same place (`LongPathsEnabled=0` on the machine). Fix: normalize BOTH sides to the same prefix form at the top of the handler — `managed_root = _lp(managed_root)` so root and every child path carry the same `\\\\?\\` prefix before any containment/write. Sweep after fix: grep for call sites that prefix children but not the root.
   - LONG-PATH `\\\\?\\` PREFIX MISMATCH — CONSUMER-READ VARIANT (S10-C4A T04A-C4-R3, verified 30/08): the asymmetric-prefix defect also bites READING paths, not just containment. The structural-compare gate built `abs_path = _Path(managed_root) / rel` PLAIN (routes:1010) while the producer writes every media/evidence file via extended-length `_lp()` — on the C4A-mandated deep runtime root (nested segment-XX dirs, artifact abs len 267–293 > 260) `Path.is_file()` returns False on the plain path even though `\\\\?\\ is_file() == True` → gate ALWAYS `RENDERED_FILE_MISSING` → `REVIEW_REQUIRED` unreachable. Classic tell: the SAME file already defines `_win_long_path()` (mirror of s09_demo_jobs) and even uses it correctly in one branch (validate-managed-artifact at :107 hash) but the gate branch forgets it. Fix: wrap the path once `abs_path = _Path(_win_long_path(_Path(managed_root) / rel))` so EVERY file op (is_file/hash/stat/decode) sees the extended form; fail-closed branches stay unchanged. Verification trap: `Path.mkdir(parents=True)` with `\\\\?\\` fails WinError 123 at >=24 level nesting, while direct write/hash/decode on the extended path works — so regression tests must EMULATE the producer by writing/hash-tagging through the extended form (helper `_lp_p()`/deep rel padding >259, never hard-code an absolute integration path), not by mkdir-chaining the deep dirs. Class rule: when a >260 path test fails, first determine which SIDE lacks the prefix (producer write vs consumer read vs root containment) by probing `plain.is_file()` vs `_lp(...).is_file()` on the SAME artifact — that one probe names the owner (T01C worker write wiring vs T04A gate read branch vs handler root normalization).
        See references/s10-c4a-t04a-longpath-reader-fix.md.
     See references/s10-c2-wrapper-hang-and-report-finalization.md.
   - FROZEN-OWNER STATIC FENCE: literal zero-error gates over "all test
     files" can deadlock on a FROZEN lane's file (S10-C4 T01C-C7-STATIC,
     verified 30/08): mypy 9-file hit literal `Success: no issues found in 9
     source files` and full S10 was 197 passed, but Ruff F* was blocked by
     EXACTLY ONE pre-existing F841 (`unused sf`) in
     `tests/test_s10_full_apply_domain.py:172` — a file owned by T01A, which
     C4 froze and did NOT list as resumable (prompt only routed T03/T04A
     errors back to their owners; it never anticipated a frozen owner's
     file). The worker did the right thing: BLOCKED_WITH_FINDINGS, named
     file:line + owner + proposed fix, and REFUSED to touch the file despite
     the fix being one line. Manager verified independently (single-error
     ruff run, ownership from registry), then asked user/Codex for one of:
     (a) narrow authorization to resume the frozen T01A owner
     `20260827_234001_9d7f39` for a static-only 1-line deletion, or (b)
     BLOCKED_SCOPE_EXPANSION. Never self-fix, never silently resume a frozen
     owner, never waive a literal acceptance. Preflight rule this exposes:
     when the prompt promises literal zero-error across ALL test files, map
     each `test_s10*.py` to its owning lane FIRST (registry write-set /
     lane TASK.md); if any test file belongs to a frozen lane, grep it for
     pre-existing F401/F841/type-ignore debt and raise the foreseeable
     deadlock in the first heartbeat instead of discovering it at the gate.
     See references/s10-c4-c7-static-frozen-owner-fence.md.
   - FROZEN-OWNER UNBLOCK VIA CODEX DECISION PACKET (S10-C4A, verified 30/08):
     when the frozen-owner deadlock is escalated, Codex answers with a
     `reviews/S10_CX_BLOCKER_PM_DECISION_*.md` packet: verdict
     `CONTINUATION_AUTHORIZED / NOT_APPROVED`, independent evidence (their own
     ruff rerun showing exactly the one known F841, focused test pass proving
     the dead line carries no behavior), exact owner + session id + the one
     permitted edit, and "do not rename/rewrite/change assertions". Manager
     flow that worked: (1) add the decision file to required reading and read
     it FULLY (it is the new authority — the bounded continuation prompt lives
     inside it); (2) re-run the prompt-mandated baseline preflight VERBATIM —
     literal 9-file mypy `Success: no issues found in 9 source files` AND the
     exact 17-file Ruff command returning exactly the ONE known error, nothing
     new (any new error = stop, classify owner, report before dispatch);
     (3) write the frozen-owner prompt with the edit pinned as "đúng MỘT line
     deletion" + explicit forbiddens (no rename of the sibling variable, no
     reformat, no rewrite, no assertion/fixture change, no other file) +
     acceptance = diff shows only that line gone + focused ×2 fresh roots +
     full S10 + diff-check; (4) dispatch with the SAME full-model-id route
     (`-m ocg/deepseek-v4-flash`, no provider flag), same owner session
     `20260827_234001_9d7f39`; (5) after worker exit, independently re-run J4
     before opening T04C. Continuation stays INSIDE the sprint id — it is not
     C5, not approval, and S11/S12/S13 stay closed.
     See references/s10-c4a-t01a-static-unblock.md.
   - T04C STRICT-HARNESS RESTRUCTURE — NO DB-WRITE/REQUEUE HELPERS (S10-C4/C4A
     T04C-C3, verified 30/08): when a vertical acceptance harness previously
     relied on `stage_c4.py` + `_force_requeue.py` + direct lease expiry /
     grace=0 (C3 era, flagged P1 by Codex), the C4A rework DELETES all of
     them. The clean shape: real fixture media (`generate_fixtures.py` →
     decodable source.mp4 + asset PNGs, `manifest.sha256` re-hashed, and the
     build validator 7/7 STILL passes after regen — a regen must not break
     the manifest); authority seeded through product models/persistence only
     (`post_seed_real_authority.py` — OccurrenceSegment 2 / SegmentMotion 2 /
     SceneGraphContact 1 / SegmentRenderRoute 6 with CHECK constraints);
     restart recovery via the PRODUCTION `POST /resume` plus the reconciler's
     real 90s swap, polled up to 420s with the spec test timeout raised to
     900s, asserting job attempt >= 2 — no direct fence/requeue, no
     terminal-as-checkpoint fallback. FAIL-CLOSED 422 IS FENCE EVIDENCE, NOT
     A REGRESSION: the smoke submit was rejected `manifest_hash mismatch:
     client '09a6c553…' vs manifest '9f77b8c3…'` because the driver passed
     the approval `checkpoint_hash` where the C6 authority-fence requires
     the `structural_lock_manifest.manifest_hash` — the harness driver must
     read the manifest's OWN hash field. During harness bring-up, classify a
     fail-closed rejection by which SIDE supplied the wrong value before
     blaming product code; a working fence rejecting a bad driver value is a
     POSITIVE signal for exactly the fix Codex asked for. Worker exited
     honest RUNNING with the one diagnosed blocker (driver fix already
     applied, not yet re-run) → resume IMMEDIATELY with the SAME prompt
     (RESUME-IMMEDIATELY rule — blocker is work continuation, not infra).
     Evidence bundle expected: ffprobe per chunk, >260 path assert, job
     attempt >= 2, structural rows probe, netstat 8201/3015/3014 cleanup.
     See references/s10-c4-t04c-c3-strict-harness.md.
   - T04C-C3 REAL-CORRECTION AUTHORITY PHASE (S10-C4A, verified 30/08): after
     the harness restructure, the NEXT failure class is the spec sending
     synthetic correction input where production now fails closed:
     (1) SPEC MUST SUBMIT REAL TYPED CORRECTION — a random `correction_id`
     dies 422 because `S10RecomputeService._resolve_correction_authority`
     (s10_recompute.py:325) requires the id to resolve to an `s09_correction`
     row with status `applied` + matching project/video + non-empty
     `affected_loop_ids` + layer match. Flow that works:
     POST /s09-corrections (`route_override`, idempotency key, target =
     real segment probed from DB) -> confirm -> read persisted
     correction_id/impact -> POST /full-apply/{run_id}/recompute with
     `correction_kind="route"`, `target_layer_ids=impact.affected_layer_ids`,
     `target_shot_ids=impact.affected_loop_ids`. (2) GENERATION SKEW in
     fixtures: seeder writes job `input_manifest_json.source_sha256` = FAKE
     hash while the real Artifact row holds the real sha → any mutation is
     blocked `stale generation` (segment source_generation=1 vs
     current_generation=2). The post-seed helper MUST sync the job manifest
     sha to the real artifact sha. (3) MASK KIND MAY BE A PRODUCTION GAP —
     probe before blaming the spec: `_validate_prompt_evidence`
     (structural_evidence.py:492) rejects `affected_region` in segmentation
     and `_render_mask_effect` (s09_correction.py:805) never writes it →
     mask correction cannot drive recompute; `route_override` was the ONLY
     kind completing submit→confirm→recompute-facts (probe verified). Worker
     must NOT patch s09_correction.py; report BLOCKED_WITH_FINDINGS with
     file:line and route to owner. (4) PROBE BYTE-DIFF BEFORE ACCEPTING
     ROUTE CHANGE: run the route-override change through BOTH adapters and
     compare bytes (sprite_affine 3288B sha 5860aead vs pose_swap 3757B sha
     9c65c7aa) — proves affected SHA truly changes and avoids the
     byte-identical-rerender trap; controlled_redraw may fail
     BACKEND_BINARY_MISSING → pick a licensed working adapter. (5) FINAL
     STRUCTURAL `BLOCKED` CAN BE CORRECT FAIL-CLOSED, NOT A PRODUCT BUG:
     `_repro_structural.py` on the run DB showed CUT_FRAMES_MISSING +
     CLIPPING_MISSING + ANNOTATIONS_MISSING because the FIXTURE's
     `structural_lock_manifest.manifest_json` had `segments:[]` and
     `mask_artifact_id=NULL` — the server correctly refused empty caller
     truth. Fix in fixture scope only: seed `cut_frames:[50]` + real
     `segments` entries + point `mask_artifact_id` at real asset PNG
     artifacts, re-sync `manifest_hash`, rerun run1/run2. Classify a
     structural BLOCKED by WHICH authority is empty (source manifest vs
     rendered vs evidence rows) before escalating: empty fixture authority =
     harness fix; empty rows after real render = product defect.
     See references/s10-c4-t04c-c3-real-correction-authority.md.
   - LINEAGE-HASH vs RAW-SHA GATE TRAP (S10-C4A T04A-C4-R2, verified 30/08):
     a real vertical run exposed a production gate regression that synthetic
     service-level tests could NOT see. The structural-compare gate added a
     binding check `if str(pub.content_hash) != str(art.sha256): BLOCKED
     (PUBLICATION_CONTENT_HASH_MISMATCH)` — but `content_hash` is a LINEAGE
     KEY in this domain, never the raw file digest: full-apply producer
     stores `sha256("pub:{run_id}:{stitch_sha}")` (jobs:903), recompute
     stores `sha256("pub-recompute:{run_id}:{correction_id}:{sha}")`
     (s10_recompute.py:1245), and the model UNIQUE constraint
     `(run_id, content_hash)` + lineage dedupe are built on that key. So the
     gate ALWAYS blocked real runs (pre AND post correction) while
     T04A-C4's `probe_direct.py` passed because it exercised the compare
     SERVICE with synthetic seeds where `content_hash == sha` by
     construction — route-binding was never covered. Manager verification
     BEFORE routing: read the producer contract lines + model constraint,
     then derive the expected lineage hash from the live DB row
     (`sha256("pub:{run}:{art_sha}") == DB content_hash` → contract holds;
     the GATE is the bug). Fix pattern: gate recomputes the expected
     lineage hash from natural_key provenance
     (`expected_publication_lineage_hash(run_id, art_sha256, natural_key)`)
     and blocks only on mismatch — raw-sha synthetic, tampered, or foreign
     provenance still fail closed. Regression test MUST go through the real
     producer path (create publication via repository with the lineage
     formula → GREEN), not synthetic `content_hash==sha` seeds. Class rule:
     whenever a new validator compares two hash fields, first resolve WHAT
     each side hashes — if any field is a lineage/formula key rather than a
     raw digest, assert the formula relationship, not equality; and any
     probe that seeds both sides equal-by-construction is blind to the
     binding defect.
     See references/s10-c4a-t04a-lineage-hash-gate-fix.md.

## C5 apply-lint & current-build exit (verified 2026-08-30)

- CROSS-OWNER LINT SPLIT: when the exact full-set lint command spans files owned by DIFFERENT lanes (features/apply + apply route page + T04B E2E + T04C E2E), each owner fixes ONLY its own slice. T04B-C2 fixed `page.tsx` `react-hooks/set-state-in-effect` + its own `s10-apply-ui.spec.ts` unused `helper`; T04C-C4 fixes only its 3 unused bindings in `s10-full-apply.spec.ts`. Manager preflight runs the FULL exact command once to record the baseline (1 error + 4 warnings, matched verbatim to Codex's review), then each worker prompt greps updates only its own files; J5 after T04B re-runs the FULL set with `--max-warnings 0` — zero/zero required, and the route page MUST be inside the set (C4's F1 was exactly its omission).
- REACT SET-STATE-IN-EFFECT FIX PATTERN (structural, no lint suppression): replace the effect's synchronous setState with React's official "adjust state during render" pattern — hold `prev` copies IN STATE and compare during render: `const [prevUrlRunId, setPrevUrlRunId] = useState(urlRunId); if (urlRunId !== prevUrlRunId) { setPrevUrlRunId(urlRunId); setRunId(urlRunId); }` (same for project). localStorage persistence stays in an effect but ONLY writes storage (never setState); URL mutations happen in user-action handlers, not effects — back/forward must not fight a replace loop. Gate evidence: zero `eslint-disable` (grep), no config weakening, TSC 0, focused UI Playwright incl. deep-link/reload/back-forward, fresh build + validator 7/7.
- BUILD_ID RENEWAL RULE: any production frontend byte change yields a NEW BUILD_ID (C4-exit `Ypg2OvkwfOy47aKRUCFMk` → C5-after-T04B `rbYCsFU8q82gvOvcRhJSA`). Vertical acceptance runs MUST cite the current NEW build (`--verify-build-only` 7/7 and `frontend/.next/BUILD_ID` match), never the previous build as current-build proof.
- BACKEND NO-WRITE BASELINE (frozen-lane drift proof): when the backend is frozen, aggregate-hash the whole backend write-set once at preflight (`sha256sum file1 … fileN | sha256sum` → ONE token, e.g. `312ea89c…` for 18 prod+test files) and re-run the identical aggregate at each gate/exit; equality = zero-drift evidence recorded verbatim in the registry. **FILE-LIST IDENTITY TRAP (C5 exit, verified 30/08): the aggregate token changes with the FILE SET — hashing only the 10 production files on a later gate yields a DIFFERENT token (`43e1ddcf…`) than the 18-file (prod + tests) preflight baseline (`312ea89c…`) and looks like drift. Save the EXACT `sha256sum file1 … fileN` list next to the token (in the prompt or registry); re-run the IDENTICAL list verbatim every time, or you chase a false drift alarm. Quick resolution when a re-check disagrees with the baseline: rerun the full 18-file list and compare tokens — no file was touched, only the set shrunk.**
- WORKER CLEANUP CLAIMS NEED VERIFICATION: a worker report may claim a probe was killed ("probe trên 8399 đã kill, port sạch") while the uvicorn is STILL LISTENING (T04C R7 probe started 14:57; cleanup claim in dispatch-r7; process alive at next preflight). During every preflight audit probe ports (8399-style) AND task ports (8201/3015); kill the straggler by exact PID only after ownership proof (command line = worktree app, listener port, dispatch-log reference), then re-netstat both the probe port and task ports.
  See references/s10-c5-apply-lint-and-current-build-exit.md.

## C6 live-UI acceptance integrity (verified 2026-08-30)

- ACCEPTANCE THEATER IS A CODEX P1 (S10-C5 PM review F1): a focused UI spec
  may pass while never exercising the workflow it names — `if (visible)`
  conditionals, permissive `.or(empty/loading/error)` disjunctions for
  progress/evidence/actions, `test.skip` for mobile, `count()===0` early
  returns, and "assert visible + non-empty helper" instead of
  `toBeDisabled()`. Green Playwright summary is NOT evidence; Codex flagged
  `s10-apply-ui.spec.ts` exactly this way after 5 pass/1 skip. The C6 fix
  packet must demand binary non-vacuous scenarios: real `toBeDisabled()` +
  enable-after-approval, UI click with observed 2xx request + durable run ID
  in URL AND localStorage AND public status API, reload/back/forward identity
  switching, real nonterminal progress vs public status response, REAL
  Cancel/Retry/Resume clicks with observed request/response + backend
  transition (separate controlled runs allowed), structural compare through
  UI reaching `REVIEW_REQUIRED` with actionable evidence + a genuine
  BLOCKED case with Review disabled, project-detail entry without count-0
  return, and MOBILE EXECUTED not skipped (390x844, overflow ≤1, helper
  visibility). Cấm `page.route`, mocked API, direct DB run/status patch,
  arbitrary sleep as truth, copied old responses, stale C4/C5 run IDs.
- BUILD-ORIGIN PORT TRAP (T04B-C3 R1, verified 30/08): the production build
  bakes `NEXT_PUBLIC_API_URL=http://localhost:8201` (run-s10.js BUILD_ENV;
  manifest envContract). Launching the suite's backend on ANY other port
  (e.g. 8212) makes the real UI fetch `localhost:8201` → `Failed to fetch`,
  an ENVIRONMENT/config error of the harness, not a production defect.
  Before blaming product code: read the build manifest `envContract` / run-s10.js
  BUILD_ENV, launch backend on the exact baked port and frontend on the
  expected port (3015 pattern), or drive via `node output/s10/run-s10.js`.
  Classify fail-closed/network UI failures by WHICH side mismatched (port,
  origin, wrong manifest field) before escalating.
- MOBILE WEBKIT VS CHROMIUM (T04B-C3 R1, verified 30/08): `devices["iPhone
  13"]` resolves to WebKit browser which may NOT be installed
  (`ms-playwright/webkit-*` missing → browserType.launch fails). For mobile
  acceptance prefer an explicit Chromium project with `viewport
  {width:390,height:844}` (Pixel-5-style) so desktop+mobile both run the
  installed Chromium; record the config so zero-skip mobile is unavoidable.
- C6 preflight before dispatching a UI-acceptance worker: (1) re-run the
  exact current focused UI suite yourself to RECORD the smell baseline
  (empty-state pass + mobile skip) — matches Codex's F1 before you can
  assign the fix; (2) inspect actual public routes from the materialized
  OpenAPI (full-apply 8 routes + s09-corrections + approvals) and canonical
  fixture/setup helpers before authoring tests — never invent API paths or
  trust report prose as product truth; (3) capture backend/migration/J1
  hashes + BUILD_ID as frozen baseline; a UI-test-only round must keep
  production source byte-identical so T04C rerun is NOT required (J6-BUILD
  branch only if production build inputs change).
  See references/s10-c6-live-ui-acceptance.md.
- LIVE-UI SUITE IMMEDIATELY EXPOSES HIDDEN PRODUCTION DEFECTS (T04B-C3 R2/R3,
  verified 30/08): once the non-vacuous suite existed (no `.or`, real
  `toBeDisabled()`, real clicks), the FIRST real run found the defect that
  every prior "green" screenshot had masked — ApplyCard.tsx:105-111 read
  `scene_manifest`/`mapping` from the snapshot TOP-LEVEL, but a REAL
  `apply_checkpoint.snapshot_json` (probe: open the run DB row, print keys)
  contains ONLY `{schema, note, compatibility_policy{policy_version,
  structural_lock_manifest_id, renderer_routes_per_segment}, warnings_accepted,
  overrides, demo_artifact_refs, correction_history_refs}` — no top-level
  scene/mapping → `selection` ALWAYS null → Apply NEVER enabled with a real
  approval. Manager verification recipe before routing:
  (1) read the frontend derivation code at the cited lines;
  (2) open a REAL snapshot row from the run DB
  (`sqlite3 ... "SELECT snapshot_json FROM apply_checkpoint LIMIT 1"` → print
  top-level keys — this one probe proves nested-vs-top-level schema truth);
  (3) then classify: UI reads wrong key shape = T04B production defect (C6
  §5.3 makes the exact owner eligible to fix it), not a harness bug. The
  acceptance-theater P1 existed precisely because the old suite never enabled
  the button to observe the broken path.
- REQUEST-ONLY REQUIRED FIELD = API-SURFACE GAP → BLOCKED_SCOPE_EXPANSION
  (T04B-C3 R3, verified 30/08): server submit binding requires
  `structural_lock_manifest.manifest_hash == slm.manifest_hash`
  (s10_full_apply.py:160-163; planner 64-hex at s10_chunk_plan.py:91-95), but
  NO public read model exposes `slm.manifest_hash` (OpenAPI scan: CheckpointOut
  has checkpoint_hash/timebase_fingerprint only; ReskinConfigData has
  `structural_lock_manifest_id` + lock_policy_version; neither equals the
  manifest hash — live probes prove BOTH alternatives 422
  `manifest_hash mismatch`). Class rule: before accepting a UI-driven submit
  flow, verify EVERY server-required identity field is reachable via a public
  read API; a required field that exists only in the REQUEST schema is a
  contract gap. Worker MUST NOT patch backend; terminal
  `BLOCKED_SCOPE_EXPANSION / PENDING_CODEX_DECISION` with three options for
  Codex: (a) expose manifest_hash in CheckpointOut/ReskinConfigData (backend
  change, owner to assign), (b) let server accept checkpoint_hash /
  timebase_fingerprint as manifest identity (contract change), (c) read-only
  DB-probe waiver for the harness (T04C precedent). Manager appends the
  options verbatim to the registry so the user can copy-paste the decision
  request to Codex. Even after the T04B-frontend fix (Defect A), Defect B
  blocks real UI submit — fix order: Codex decision first, then the same
  owner resumes, then J6-UI → J6-BUILD (production frontend changed) →
  T04C-C5 two current-build runs.
- C6 BLOCKER CLEANUP BEFORE REPORTING: after the R3 blocker, Manager verified
  and killed the suite's owned backend uvicorns (PID 36444 port 8213 + PID
  31956 port 8201, plus bash wrappers) using exact-PID + command-line + port +
  dispatch-log launch-record ownership proof, re-nettat both probe and task
  ports, and confirmed only infra processes (9Router, hermes desktop/serve,
  MCP, Codex CUA) remained. Registry append carried the full blocker state +
  decision options + cleanup; terminal stayed
  `BLOCKED_SCOPE_EXPANSION / PENDING_CODEX_DECISION` — never a green claim.
  See references/s10-c6-live-ui-defect-discovery.md for the full Defect A/B
  verification recipes and the copy-paste decision options for Codex.

## Exclusive write-set discipline
- Every task prompt carries VERBATIM allowed/forbidden paths from its TASK.md.
- Before launch AND after exit: `git status --porcelain` audit; modified files
  outside the lane's allowlist during the run window = incident → kill, report,
  relaunch tightened.
- Parallel lanes must have disjoint write-sets; shared-file edits wait for the
  owning lane's writer to exit.

## Join gates / freeze manifests

- J1-v4 re-hash gate: run `scripts/j1v4_rehash.py` (packaged with this skill)
  for the direct 13/13 byte + EOL check (12 LF + composite.py CRLF) — it
  reads `output/s09/20260823_sprint_full/freeze-c4-meta/freeze_manifest_v4_after.json`
  under the integration worktree and prints per-file OK/DRIFT + EOL, exit 0
  only on full pass. Preflight AND final exit gate both use it.
- Pin machine-readable manifests: JSON `{path: sha256}` over every
  behavior-critical file recursively, plus frozen_at + HEAD sha. A prose SHA
  token in a registry breaks silently when any file changes later.
- Versioned manifests need lineage fields: `version`, `supersedes` (v1 name +
  SHA), `reason` for the re-pin. Keep old manifest files on disk — downstream
  records cite v1 SHAs and must stay auditable.
- Workers must verify manifest before AND after each measured run; drift ⇒
  stop, invalidate ALL downstream runs/decisions, fix via the file's owner,
  re-pin a v2 manifest, full rerun. Never patch the manifest itself.
- When a correction legitimately touches frozen surface mid-cycle (e.g. adding
  per-region occluder placement after an honest f5 fail), flow is: document
  measured v1 → contract-owner correction → J1-v2 pin → FULL A/B rerun → only
  then downstream decision tasks.
- Drift discovered LATE (e.g. at final gate) is a disposition question, not an
  automatic full-invalidate. Attribute first: mtime of the drifted file +
  grep of lane logs for who wrote it and when. If (a) the change predates the
  measured runs it would taint, AND (b) the owning lane DISCLOSED it in its
  REPORT under a named escape clause (e.g. "production failure bắt buộc"
  write-set deviation), AND (c) the diff is additive/behavior-neutral for the
  frozen surface — then re-pin the NEXT manifest version (v3, lineage fields)
  including current state and move on. Undisclosed drift, or drift written
  AFTER the measured evidence it would taint, still means invalidate +
  owner-fix + rerun everything downstream.
- One freeze AUTHORITY only — split-brain kills a cycle silently. Coexisting
  authorities (Manager J1 JSON + legacy three-file contract_freeze_manifest +
  prose SHA tokens in old registries + script auto-detect fallback chains)
  mean a re-pin leaves downstream evidence citing the OLD sha: C2 shipped a
  v3 manifest while EVERY measured row and decision doc still pinned v2.
  After each re-pin, rg the previous SHA across output/decision/binding
  artifacts and resume owners to rebind BEFORE accepting the lane. Measured
  CLIs take manifest path+SHA as explicit args from the Manager packet —
  no newest-scan, no v2→v1 fallback, no three-file manifest, no prose lookup.

## Terminal-state protocol

- Prompt rules override instinct: if ANY required class ends fail/unknown/FOQ,
  terminal is `BLOCKED_WITH_FINDINGS`, NOT manager-verified — even when every
  static gate is green. Grep your own result JSONs for FAIL_OPEN/FOQ/unknown/
  CONTRACT_REJECTED before writing any terminal line.
- Allowed terminals are exactly what the authorizing prompt states (usually
  `TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` or
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`). No APPROVED/CLOSED, no push.
- PREP-phase workers must stop at `WAITING_JOIN` (or an explicitly phased
  STATUS), never `TASK_SUBMITTED`, and must not run global gates while other
  writers are active. Final binding runs happen only after the decision task
  verifies — dispatch them as a separate resume of the same owner session.

## Evidence verification (run these yourself, every time)

- SWEEP-CHAIN EXIT TRAP: a `cmd && grep -c SYMBOL file && cmd2` chain dies
  silently when `grep -c` counts ZERO — grep exits 1 on empty matches, so
  the remaining gates never execute exactly when the sweep proves the defect
  is gone. This cost a C4 Manager preflight sweep (chain stopped after the
  zero-count `type: ignore` check; the J1/alembic/ruff gates had to be
  re-issued as separate commands). In multi-gate sweeps either append
  `|| true` after every zero-is-success `grep -c`, or split gates into
  standalone commands — never assume later links ran because earlier ones
  printed.
- PIPE-EXIT-CODE MASK — `$?` after a pipeline measures the LAST command, not
  the gate (verified 30/08, C5 baseline): `npm exec eslint … 2>&1 | tail -30;
  echo "ESLINT_EXIT=$?"` printed `ESLINT_EXIT=0` while the tailed output showed
  `✖ 5 problems (1 error, 4 warnings)` — tail exits 0, masking eslint's exit
  1. ANY `cmd | tail/head/grep` + `echo $?` re-reads the pipe's tail exit code
  and can turn a RED gate green in your own evidence. For gates that must be
  exit-code-provable run the command with NO pipeline (or `; echo $?` after
  the bare command, or use `set -o pipefail`), and when you must tail long
  output, capture exit first: `cmd > log 2>&1; echo EXIT=$?; tail -5 log`.
  Reading the tail TEXT ("All checks passed!") is acceptable as content
  evidence, but never pair it with a misleading `$?`.
- Read result JSONs directly: count MEASURED_RENDERED_OUTPUT per risk class;
  check per-class `overall_pass`; adversarial controls must be
  FAILED_AS_EXPECTED; diff run_A vs run_B after stripping exactly the declared
  non-deterministic fields (all-runtime-field diffs = determinism PASS).
  Strip RECURSIVELY: timing fields nest at multiple depths (row-level
  `wall_time_ms_total` plus `runtime_ms_per_frame_measured`,
  `wall_runtime_ms_per_frame`, run-specific artifact paths inside per-row
  backend objects) — a shallow top-level-key strip leaves nested noise and
  produces a FALSE determinism-fail on byte-identical content (C3 I03:
  18 residual diff lines, all timing/path, zero content deltas). When the
  structural verdict stays ambiguous, decoded content-hash equality
  (run_A hashes == run_B hashes per fixture/route) is the decisive ground
  truth: bytes equal ⇒ deterministic, whatever the remaining field noise.
- Provenance completeness per record: route, adapter/backend id, license,
  request-contract SHA, manifest SHA, encoded-artifact SHA, canonical
  decoded-frame SHA, frame count, rational fps/timebase.
- Benchmarks must instantiate the public router and call execute(); direct
  compositor/private-helper calls invalidate the evidence.
- Gates ×2 with separate basetemp dirs, DB env unset, encoding modes both ways
  (PYTHONUTF8 unset vs =1). Re-run everything touched after the last edit.
- STALE-VERIFICATION SIGNATURE — "N passed ×2" that PREDATES the last edit is
  not a pass (S10-C4 T04A-C4, verified 29/08): worker fixed an F841 (deleted
  2 unused vars in routes) AFTER run2 had already completed, kept claiming
  `54 passed x2`, but then honestly reported the gap ("lần 2 chạy TRƯỚC khi
  sửa F841"). Manager rule: when a worker report mentions ANY code edit after
  the last recorded pytest run, cross-check mtime order —
  `ls -la --time-style=full-iso <source-files> <test-log>` and require the
  test log to postdate the newest source edit; otherwise resume the SAME
  owner with a rerun-on-final-tree packet ("chạy lại pytest x2 trên đúng cây
  cuối") before any J-gate. Same shape as the T01C-C6 iteration-cap case but
  with the tests already green — the cliff is accepting counts computed on a
  superseded tree.
- SELF-DISCLOSED MISSING EVIDENCE LOGS (S10-C4A T04A-C4-R3, verified 30/08):
  a worker can state "các con số đều là thật; đây chỉ là thiếu file log vật lý
  trong bundle" — suites ran green inside the session but the redirect only
  captured some logs (T03 bundled, T01C/T02/T01A logs omitted). Treat the
  admission as a REAL evidence gap, not a dismissal: do NOT accept the bundle,
  re-run the missing suites yourself and write the logs into the evidence dir
  (Manager-side `pytest_retained_manager.log`), then note the compensation in
  the registry. A green number without its raw log is still an unverifiable
  claim until re-run.
- PER-OWNER MYPY ISOLATION for carry-forward routing (S10-C4 J2, verified
  29/08): `mypy <owner_file>` FOLLOWS IMPORTS, so errors reported against
  imported OTHER-owner files (e.g. `mypy s10_recompute.py` listing 8 errors
  in `s10_structural_compare.py`) do NOT belong to the lane under audit.
  Run twice: (a) isolation form `python -m mypy <owner_file>
  --ignore-missing-imports --follow-imports=skip` → `Success: no issues
  found in 1 source file` proves the owner is clean on its own surface;
  (b) full follow form piped to attribution
  `... 2>&1 | grep 'error:' | awk -F: '{print $1}' | sort | uniq -c` →
  file-level counts that decide which owner's resume packet carries which
  carry-forward. Record both commands in the registry; never route an error
  to an owner just because it SOUNDS related to the file being checked.
- Machine decision artifacts get their own three-point audit before opening
  any join gate: FOQ count == 0; every entry PASS with non-null smallest
  passing route; manifest match_expected == true with rehash count ==
  file total. Pin the decision-file SHA and quote it verbatim in every
  downstream resume packet with an explicit "no prior-cycle fallback" clause.
- Provenance in decision docs may be NESTED, not top-level: C3 I05 kept the
  manifest/run pins under `independent_verification` and reference-media
  status under `reference_states`, so checking only `inputs`/`provenance`
  keys reported false-missing. Fast locator: whole-doc string-scan for the
  expected SHA/path tokens to find where provenance actually lives, then do
  the structured audit there. Same scan doubles as the stale-pin check:
  grep the doc for EVERY prior-cycle SHA/path (v2/v3 manifests, old run
  dirs) — zero hits is the negative assertion Codex will re-run.
- When counting measured passes per risk class, exclude adversarial/control
  rows first (C3 runs carried 6 measured MEASURED_RENDERED_OUTPUT + 6
  adversarial CONTRACT_REJECTED rows per run — counting raw rows
  double-counts every class).
- Run the rg/superseded-evidence gate BEFORE drafting any terminal line —
  never after "all gates look green". Passing tests do NOT prove clean
  evidence lineage: on C2 the final gate caught two T02 test files still
  LOADING the superseded v1 artifact (`t00-i05/measured_seed20260823`) as
  frozen input while every suite passed, purely because the old file still
  existed on disk. Grep active code+tests for prior-cycle paths; archival
  docs/logs exempt; resume the owning session for a pointer fix.
- Independent decoded-frame hash verification must use the project's PUBLIC
  canonical decoder (e.g. `renderer_routes.composite.decode_rgb_frames`)
  AND the PRODUCTION canonical hash FUNCTION (e.g.
  `composite.canonical_frame_sha256`) — never an ad-hoc `ffmpeg -f rawvideo
  -pix_fmt rgb24` dump (raw pixel ordering/format differs) and NEVER a
  hand-rolled reimplementation of the hash algorithm. C3 final gate 3c: a
  self-written mirror that omitted per-frame
  `np.ascontiguousarray(frame).tobytes()` reported 6/6 FALSE mismatches on
  byte-perfect artifacts; switching to the real production function flipped
  all six to True in one run. First mismatch = check decoder AND
  hash-function choice before suspecting the evidence.
- Canonical-hash FIELD SEMANTICS are a review target, not just decoder choice:
  if production defines the canonical hash as (frame_count + ordered frame
  shape + contiguous bytes) and the harness stores a raw-concat hash in the
  same-named field while putting the adapter's hash in a different field,
  every "MATCH" claim is meaningless — two hashes of different byte streams.
  Codex recomputes both independently. C3 contract: independent recompute must
  mirror the PRODUCTION algorithm exactly AND assert equality with the adapter
  evidence per row; add an adversarial test pinning the field to the canonical
  algorithm so raw-concat cannot silently return.
- Verify MAIN/data untouched with an mtime-vs-checkpoint probe instead of
  interpreting git-status noise: `find <protected roots> -type f -newer
  <join-manifest-or-checkpoint-artifact>` — empty output proves nothing in
  the protected tree changed since the pinned artifact regardless of how
  dirty the worktree was at preflight.
- DB probe pitfalls (verified T06B-C4 27/08): (a) `WHERE id IN (?)` with a
  tuple bind fails on SQLite — expand to `WHERE id IN (:jid0,:jid1…)` with
  one placeholder per id; (b) `job_attempt.step_code` for regen jobs is
  `run` in the isolated QA DB (`DEMO_STEP_CODE`/`REGEN_STEP_CODE` = `run`
  for that job_type) — counting `demo_loop_regen` yields 0 and falsely
  claims no renderer pass; probe must count `run` for those jobs (see
  `s09_demo_jobs.py:91-92,123,1877-1881` and `db_attempt_probe.py` regen
  counting).
- Alembic CWD trap (verified S10 J1 28/08 00:28): `alembic.ini` uses
  `script_location = migrations` (relative). Running `alembic heads` from
  `C:/Users/Admin/MotionForge2D` (MAIN, 4 migrations) returns
  `d5e6f7a8b9c0 (head)` and hides the 13 worktree-only revisions; running
  from `C:/Users/Admin/MotionForge2D-worktrees/s08-integration` correctly
  returns `a10b11c12d3e (head)` with the full 17-file chain. Every J1/migration
  gate must `cd <worktree>` before `alembic heads/history/current/upgrade` —
  never run alembic from MAIN cwd when the worktree is the integration
  authority. `find` + `grep` of file-level `revision`/`down_revision` is
  not a substitute; verify via `ScriptDirectory.from_config` if unsure.
- Pytest invocation trap (verified S10 J1 28/08 00:28): this project's
  `pyproject.toml` addopts break bare `pytest --cache-clear` (`unrecognized
  arguments: --cache-clear`). Correct isolated re-verify is
  `pytest <tests> -v -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>` .
  `--cache-clear` without `-p no:cacheprovider` fails; bare `--basetemp`
  without override inherits `addopts` and can break. Use this exact form for
  every ×2 gate and record the basetemp path in the registry.

## Registry & heartbeats

- Maintain a session registry markdown: lock table (task→session→proc→state→
  write-set), decision log with timestamps (+07), verify results with real
  numbers ×2 runs. This registry doubles as the Codex review-packet skeleton.
- Append to shared registries/logs with shell heredoc (`cat >> file <<'EOF'`).
  Never patch-replace a line you appended earlier in the same run — concurrent
  appends (yours + workers') make patch fail with stale/identical strings;
  re-read before any structured edit of a shared file.
- Heartbeat ≤20 min while any lane is active: status table + blockers + next
  action. Answer ETA questions lead-with-status + concrete table; run `date`
  first — never invent timestamps. Vietnamese ETA triggers include `essti`/`esti`/`es ti` (typo/no-diacritic for "estimate"),
  `at` (typo/shorthand for ETA), `baoh xong`/`bao h xong`/`baoh` (no-diacritic for 'báo xong'), `sap xong`/`sắp xoiong chưa`/`sắp xong chưa`/`bao giờ thi xong`/`bao gio thi xong`/`bao giwof thi xong hết` (no-diacritic/typo for 'sắp xong chưa' / 'bao giờ thì xong'), `up date`/`up darte`/`updarte`/`up-date` (typos for 'update'), `bao gio xong`, `estimate`/`est`, `có ổn ko`/`ổn ko`/`có ổn không` (status check — lead with status table, then ETA) —
  all require an instant date-anchored wall table (ideal vs +1 correction)
  co-located with dispatch confirmation, not deferred to heartbeat. When scope
  grows mid-sprint say so plainly and update the ETA rather than defending the
  old one.
  MotionForge2D S09-C4 Muse (26/08): user requested **heartbeat every 5 minutes**
  when coding feels slow (`heartbeat mỗi 5 phút đi tôi thấy coding chạy hơi chậm`)
  — honored 5' for Muse phase. **S09-C4-META (27/08): user updated to heartbeat
  every 30 minutes + immediate on lane exit / blocker**
  (`nhớ heartbeat mỗi 30p để báo cáo kết quả cho tôi hoặc khi có task gì đó xong
  hoặc có vấn đề`) — honor **30' cadence + instant notification on task
  completion or blocker** for META completion; do not retain 5' for this phase.
  Slow coding is expected with reasoning `max` (150k-token prefill needs 900s
  TTFB, 15–22 min silence before first burst is normal, not a stall).
  **Continuous execution (27/08 META): user repeated `chạy đi đừng tự dừng` / `xong chưa` mid-DAG — manager must keep polling (`process wait` loops) and resume same owner session immediately on any stall/exit, not wait for next heartbeat interval; every user go-command gets instant dispatch confirmation + ETA table in the same reply.**
  **S10 Full Apply (27/08 22:13–23:59): same 30' + instant, `meta/max/TTFB900/fallback OFF`, T01A‖T01B disjoint parallel only (max 2 writers) then serialized — user expects date-anchored ETA wall table on every go+ETA co-occurrence and proactive 'đang chờ gì' when parked between phases; silence without stated wait reason triggers 'sao thấy dừng rồi?'. Gateway 524 = RUNNING_RETRY_WAIT per Rules §7 (wait 5' then same-session resume, not new session); T01B 26×2 pass is reference for deterministic planner purity (no DB/IO/time/process/path, canonical JSON sort_keys). J1 (28/08 00:30) verified 47 passed ×2 with alembic-cwd + pytest-invocation + prompt-file heredoc lessons captured below — never derive terminal from worker stdout alone; re-run `cd <worktree> && pytest … --basetemp` yourself.**
- When a worker's own REPORT/LOG reveals it exited early with unfinished work
  (root-caused blocker, "chưa xong", remaining steps listed), do not treat its
  TASK_SUBMITTED as terminal — resume the owner immediately with a packet that
  (1) restates ITS OWN root-cause verbatim, (2) lists the exact remaining
  steps, (3) names the correct STATUS for the phase. Same for a worker that
  exits mid-gates. The registry records these as "<task> DONE + verify PASS"
  only after YOUR OWN re-run of the decisive command passes.
- Write-set deviations: when a worker touches files outside its allowlist,
  check whether it DISCLOSED the deviation in its REPORT with a named escape
  clause and a technical justification before flagging an incident. Disclosed
  + justified + behavior-neutral = accept and record in registry (and re-pin
  freeze manifests if the file is under one). Silent out-of-set writes remain
  an incident → kill, report, relaunch tightened.

See references/pm-correction-cycles.md for verified S09-C1/C2 case notes
(terminal-state F1 incident, freeze-manifest evolution, honest-f5 scope-growth
loop, schema-bump/seeder-case incidents, evidence-audit snippets).
See references/s09-c2-full-cycle.md for the complete C2 arc (one-day terminal,
late-drift disposition path, worker-early-exit handling, registry-as-packet).
See references/s09-c3-unified-freeze-cycle.md for the C3 round (single freeze
authority v4 dispatch packet, targeted-regeneration contract pattern,
long-path read/serve gate, F6 terminal-evidence hygiene rules) plus the
verified C3 outcomes: T05A canonical-context suite landed in a NEW test file
(grep tests/ by function name — don't assume coverage lives in the old domain/
api/c1 files), I03 determinism needs a DEEP recursive strip of timing/path
fields before any A/B verdict (shallow strip yields false FAIL; decoded-hash
equality A==B per fixture/route is the decisive tiebreaker), and the
acceptance-lane findings→owner-routing loop: T06B found three contract
defects (F1 required client pin bricking the UI, F2 replay reused=false, F3
BE approval matching 2 of 4 FE reason sources) AFTER every unit/static gate
was green — each confirmed in code at file:line, routed to its exact owner
with ONE prescribed fix + forbidden alternative, then the frozen E2E spec
re-run unchanged. Owner lookup for lanes not named in the prompt:
`ls docs/pm/sessions/ | grep -i <component>` + grep for
`[0-9]{8}_[0-9]{6}_[a-f0-9]{6}`.
See references/s09-c4-exact-scope-regeneration.md for the C4 round (C3 review
F1–F7 findings incl. byte-identical-rerender-vs-reuse and non-discriminating
acceptance evidence, five-kind render-effect dispatch contract, three-part
fingerprint with frozen_evidence_sha256, `-q` vs `-z` CLI flag drift that
EXIT=2'd a whole wave, router-wide TTFB stall classification =
RUNNING_RETRY_WAIT don't-kill).
See references/s09-c4-muse-completion.md for the Muse-routed C4 FULL completion (J0-MUSE reconcile, 9Router credential injection vs curl probe, 900s TTFB for 150k-token prefill, exact-owner `hermes --resume` with `muse`/`ocg/muse-spark-1.2-contributor`, `wire_extraction_segment` = `create_extraction_segment` alias and `REQUIRED_JOB` bypass via `user`/`manual`).
See references/s09-c4-meta-completion.md for the META-routed C4 completion (J0-META + 7-file CRLF→LF byte-freeze `ae92247b` diagnostic, combo `meta` round-robin `cmc/meta`+`ocg/muse-spark-1.2-contributor`, heartbeat 30' + instant on exit/blocker, T04 23-test integrity + T06B probe `IN (?)` and `step_code run` vs `demo_loop_regen` fix).
See references/s09-c5-bounded-correction.md for the C5 bounded correction (F1 long-path ≥260 via `_win_long_path` at `s09_demo_jobs.py:1306-1310` → bind `1871-1877` must use same contract + d4-only regression; F2 zero-mutation `>=`→equality via single transaction/savepoint before any commit; F3 frozen-evidence canonical = `decision content SHA + run-A content SHA + run-B content SHA` only, no filesystem path — same bytes at different path = same ID; F4 deterministic launcher + isolated runtime root/DB/output/ports with captured logs + `finally` cleanup on Windows PowerShell/Node surface — no generic `bash` via WSL; F5 Ruff I001/E501 at 558/606/610/776/825/830 + mypy unused-ignore at 776 within T03 write-set; F6 registry quiescence — final table with no `PENDING`, evidence persisted before claim, only attributed QA trees killed).
See references/s09-c5-r2-parallel-prep.md for the C5-R2 maximum-safe parallel PREP wave (371-line prompt, `J0 -> [T03||T04||T06B] PREP -> B1 -> J1 mutex -> J2 -> T06B x2 -> J3`, max 3 only in P-C5, disjoint write-sets, unique temp/DB/ports, B1 quiescence + write-set hash audit, 20' heartbeat + instant on exit, `write_file` not bash heredoc for prompts).
See references/s09-c6-exit-hardening.md for the C6 exit hardening (EOL guard `text eol=lf/crlf` durable 13/13 direct, process-ownership no kill-by-port, per-run runtime/DB/output isolation, coherent identity with real byte hashes, J3 evidence hygiene).
See references/s09-c6-execution-addendum.md for C6 live execution pitfalls hit after dispatch (`.gitattributes` B1 exclusive-owner violation 28→13, `eslint.config.mjs` cwd requirement, terminal 180s cap vs 77s suites, `npm.cmd` on Windows, `from app.api.app import app` not `create_app`, heredoc EOF vs `write_file`, T04 gated though not dispatched).
See references/s09-c5-final-gate-crlf-and-windows-pitfalls.md for C5 final-gate Windows pitfalls (mixed CRLF/LF freeze `max(raw,lf)` 13/13, basetemp prefix too long → `OSError` after 10 tries, `.codex-review` deep nesting breaks `rglob`, TSC/ESLint Windows `node .../bin/*` invocation, heredoc EOF with quotes, T06B x2 production logistics + J3 10/10 sequence).

- Frontend static gates on Next.js: a `tsc --noEmit` failure inside
  `.next/dev/types/validator.ts` (TS1128 or similar) is STALE GENERATED
  output, not source code — `rm -rf .next/dev/types` (or the whole
  `.next/dev`) and re-run before reporting a TSC gate failure. Verify the
  error's file path is outside `src/` first; never let generated-file noise
  fail a lane's static gate.
- ESLint scope discipline: run the gate S09-scoped (`npx eslint
  "src/features/demo/**" --max-warnings 0`) — a full-repo `npx eslint src`
  sweep counts PRE-EXISTING warnings from unrelated features and will fail
  the lane through no fault of its write-set. If you do run full-src for
  visibility, report it as informational only and record in the registry that
  out-of-scope warnings are pre-existing; never let a broadened lint surface
  retroactively fail an already-green gate. Also note `next lint
  --max-warnings 0` errors with "unknown option" on current Next — use plain
  eslint directly. PRE-EXISTING-ERROR CLASSIFICATION (S10-C4A exit, verified
  30/08): when an exit-gate lint command is BROADER than the precedent scope
  (e.g. adding `src/app/(app)/apply/**` to the existing `features/apply/**`
  gate) and fails, classify by mtime vs sprint start + git-status ownership
  BEFORE calling it a regression — `page.tsx:90` react-hooks
  set-state-in-effect was dated 2026-08-29 03:16 (pre-C4, T04B-owned frozen),
  so the precedent-scoped gate stays the PASS evidence and the broader error
  becomes a named carry-forward P2 for Codex, never a self-fix of a frozen
  owner. Full recipe in references/s10-c4-exit-gates-and-eslint-scope.md.
- Registry & evidence hygiene (C2 review F6): terminal timestamps must not
  precede later append actions — write the terminal line LAST, after cleanup
  and all registry rows; dedupe registry entries in the same pass (patching
  appended lines fails on identical strings — use heredoc append + one
  dedupe/fixup script at the end); never quote suite counts from memory
  (collect the resolved test file list fresh each gate — C2 claimed 23 files/
  356 tests while the checkpoint collected 363); never claim "ports free" or
  "0 processes" without a same-turn netstat/wmic check. Codex audits these.
- C2→C3 verdict correction: with any open FOQ or required-class fail, the
  terminal is `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW` even if every
  other gate is green — Codex re-labeled C2's TASK_MANAGER_VERIFIED to
  BLOCKED_WITH_FINDINGS on exactly this rule. Also: a "MATCH" between two
  hash fields is only meaningful if both fields hash the SAME byte stream
  (see evidence-verification section for the canonical-vs-raw-concat trap).

## C3 verified outcomes (26/08 early morning)

- T05A context service: `applied_regeneration_context()` returns canonical ctx
  (affected lists sorted+dedup, effect = mutation result,
  `context_sha256` = sha256(canonical JSON minus the sha field itself)) —
  deterministic across fresh sessions; new suite
  `test_s09_t05_backend_c3_context.py` 11 tests ×2 PASS.
- I03-C3 measured on v4: 6 measured MEASURED_RENDERED_OUTPUT + 6 adversarial
  CONTRACT_REJECTED per run; canonical==adapter hash 12/12 rows; every row
  pins j1_manifest_path=v4 + exact SHA; post-run manifest drift NONE.
- Determinism audit recipe that worked: deep-strip timing/path fields
  (`wall_time_ms_total`, `runtime_ms_per_frame_measured`,
  `wall_runtime_ms_per_frame`, `artifact_path`, `run_dir`,
  `j1_manifest_path`, `adversarial_artifact`) at ALL dict depths → structural
  identical True; plus decoded-hash equality A==B per fixture/route as the
  independent tiebreaker. A shallow top-level strip showed a false FAIL first —
  never issue a determinism verdict while the two checks disagree.

## Phased dispatch of one owner across a cycle (C3 pattern)

- One owner session may need MULTIPLE resumes per round, each a distinct
  phase with its own prompt file: PREP (scaffold + independent fix) →
  FINAL INTEGRATION (after its upstream join opens) → FINAL BINDING (after
  the decision task pins). Write each phase as `prompt-prep.txt` /
  `prompt-final.txt` / `prompt-binding.txt` in the lane dir; never bundle
  all phases into one giant prompt — the worker can't know upstream results
  that don't exist yet, and PREP-phase workers must stop at WAITING_JOIN.
- In each phase packet, state what CHANGED since the last phase by exact
  symbol/location (e.g. "T05A service merged: applied_regeneration_context()
  at s09_correction.py:585 — replace your stub/adapter with a real call"),
  plus the frozen chain SHAs verbatim. The worker's next resume otherwise
  re-derives stale assumptions from its old context.
- Join-gate readiness = BOTH upstream lanes exit AND Manager-verified; only
  then write the join-open line in the registry and dispatch the downstream
  resume in the same turn.

## Acceptance-lane findings → owner-routing loop (C3 verified ×3, 26/08)

Production acceptance lanes exist to FIND contract defects — expect 1–2 extra
rounds even after every unit/static gate is green. The loop that closed C3's
last three findings (T06B F1/F2 → T04 fix → rerun → F3 → T06A fix) in one
morning:

1. An acceptance worker hitting a defect OUTSIDE its write-set reports
   `STATUS: BLOCKED_WITH_FINDINGS` with per-finding evidence + a one-line
   "việc cần để mở khóa". That is the DESIRED outcome — never push an E2E
   lane to force a pass (Codex's C2-F1 complaint was exactly that).
2. Manager confirms each finding IN CODE before routing: read the exact
   schema/service lines cited (all three C3 findings confirmed at file:line
   within minutes).
3. Route each finding to its EXACT owner as a resume carrying root cause
   (file:line) + ONE prescribed fix + forbidden alternative — e.g. "(a) make
   the client pin OPTIONAL, the server already pins via the decision SHA
   chain; do NOT make the frontend send it, that violates the
   body-only-correction_id contract". A single prescribed option prevents
   the owner re-litigating the design.
4. Owner lands fix + regression tests; the acceptance lane RE-RUNS THE SAME
   frozen spec — never rewrite the spec to match the bug.
5. Owner lookup for lanes NOT named in the prompt: `ls docs/pm/sessions/ |
   grep -i <component>`, then grep that dir for
   `[0-9]{8}_[0-9]{6}_[a-f0-9]{6}`.

Contract-drift subclass (F3): when one side of an API contract gains accepted
sources (FE `reasonsOf` matching reasons[] / override_reason /
provenance.reasons / provenance.evidence), grep the OTHER side for the same
source list before declaring done — BE still matched 2 of 4 sources and
approval-overrides failed only in full E2E.

Related API contract lessons (verified fixes): server-side SHA-chain binding
makes a REQUIRED client copy of the same pin redundant friction (make it
`str | None = None`, verify when present); idempotent-create replay must
return `reused=true` consistently; FastAPI double-decorator `/x` + `/x/`
yields two OpenAPI paths for ONE handler — intentional aliasing, not a dup
defect (confirm the shared endpoint function before flagging).

## Stray-process cleanup (final gate)

- Kill by exact PID only (`powershell -Command "Stop-Process -Id <pid> -Force"`).
  `taskkill //PID` from MSYS bash fails with "Invalid argument"; `cmd //c
  taskkill` prints a banner and may not execute. Never killall/pkill python —
  the agent itself runs on Python.
- Identify strays by command line, not name: `wmic process where
  "name='python.exe'" get ProcessId,CommandLine | grep -E "uvicorn|pytest|
  playwright|s09"`. A leftover `uvicorn app.main:app --port 8099` from an old
  QA lane looks identical to a live worker until you read the full CommandLine.
  Verify ports with netstat after killing; record the PID + port in the
  registry cleanup line.
- Flag TEST-ONLY SERVERS specifically: a leftover
  `uvicorn output.<lane>.qa_app_patch:app --port 8099` is doubly notable —
  it is both a stray process AND evidence a lane used a QA app patch /
  test-only router that most sprint prompts forbid ("không dùng QA app
  patch/test-only router"). Kill it AND name it in the registry cleanup row so
  Codex can see whether the forbidden surface leaked into acceptance evidence
  (C3 final gate caught exactly this from a PREP phase two rounds earlier).
  A production-app uvicorn (`app.main:app`) and a qa_app_patch uvicorn are
  NOT the same finding.

## Manager silence between phases (user expectation)

- The user watches progress and WILL ask "sao thấy dừng rồi?" if no visible
  message lands for a while. Silence has only three legitimate causes:
  workers running, waiting on a join gate, or parked at terminal awaiting
  Codex review — STATE WHICH ONE proactively in the heartbeat that closes a
  phase ("đang chờ T04 exit để mở J2", "terminal xong, đang chờ Codex").
- When the user says "chạy đi" (or any go-command) TOGETHER with an ETA
  question, answer BOTH in that same first reply: dispatch confirmations +
  ETA table immediately; do not defer the estimate to a later heartbeat.
- After writing a terminal state, say explicitly that stopping is protocol,
  not idleness: list what is done, what is awaited, and who owns the next
  move (Codex review). This converts "40 minutes of silence" from a bug
  report into an expected state.

## C3 cycle closed (26/08 morning) — final numbers for the record

Full arc: preflight (rules SHA 987386c5…, HEAD ee10e55a) → J1-v4 pin
(ae92247b…) → Wave A ×5 → I05 (FOQ=0, decision SHA d289929d…) → T04 phased
PREP→FINAL→BINDING (one §7 stall-recovery mid-way, zero progress lost) →
acceptance loop F1/F2→T04 + F3→T06A → T06B rerun-3 Chromium ×2 PASS with
verified before/after evidence JSONs. Three contract defects found and fixed
AFTER all unit/static gates were green — see the acceptance-loop section.
Complete session detail lives in references/s09-c3-unified-freeze-cycle.md;
the C2 review's F1-class lesson ("acceptance asserted the inverse") is what
made rerun evidence audits mandatory: verify changed/unchanged per loop in
the JSON yourself before believing a green E2E line.

## Final-gate canonical recompute (verified C3 gate 3c recipe)

The exact Manager-side independent verification that closed C3 (run AFTER all
workers exit, BEFORE any terminal line):

```
import hashlib, sys
sys.path.insert(0, ".")
from pathlib import Path
from app.services.renderer_routes.composite import (
    decode_rgb_frames, canonical_frame_sha256,
)
for r in results["results"]:
    if not r.get("decoded_output_hash"):
        continue  # skip adversarial/CONTRACT_REJECTED rows
    frames = decode_rgb_frames(Path(r["artifact_path"]))
    canon = canonical_frame_sha256(frames)   # production function, not a copy
    assert canon == r["decoded_output_hash"] == r["adapter_output_frame_sha256"]
```

Key properties: uses ONLY public surfaces (public decoder + production hash
function), skips non-measured rows, and asserts the THREE-way equality
(independent recompute == harness stored field == adapter self-report) that
Codex's C2-F3 finding demanded. A mismatch after this is an evidence defect;
a "fix" that edits your own recompute helper until it matches is fake
independence — Codex will re-run it.

## C7 owned-restart machine-checkable evidence (verified 2026-08-27)

Run PASS does not equal evidence PASS. S09-C7 prompt §6 requires per-run artifacts beyond `.last-run.json status=passed`:

- **Chromium green but schema red**: Run1 18:15 + Run2 18:16 both passed discriminating assertions (35s spec, `lifecycle initial 29080→29740 / 4652→32580`, `initial!=replacement`) yet J3 audit 18:35 found `lifecycle.json` had only 10 keys (`runTag, backendPort, frontendPort, worktree, runRoot, initialPid, replacementPid, alternatePid, frontendPid, frontendLogPath`) — missing mandatory `listenerOwnerBeforeRestart, listenerOwnerAfterReplacement, replacementListenerPid, initialStopTimestamp, replacementLaunchTimestamp, finalExited, portReleased, checkpointCreatedBeforeInitialExit, checkpointReadAfterReplacement, rendererAttemptCount`. Fix: resume exact owner `20260824_131423_423e42` with `meta/max/TTFB900`, extend spec to capture `listenerOwnerPid(BACKEND_PORT)` before `stopLaunched(initial)` and after `waitForPortListenerOwnedBy(replacement)`, timestamp `Date.now()` at stop/launch boundaries, assert `initialPid !== replacementPid`, `replacementListenerPid === replacementPid`, `initialStop < replacementLaunch`, `finalExited.* === true`, `portReleased.* === true` before writing, then re-run fresh `node output/.../t06b-c7/run-c7.js --run run1|run2` sequentially for new runTag/PID/DB — never copy old C6 artifacts.
- **Isolated runtime decision binding**: helpers `launchIsolatedBackend` must set `MOTIONFORGE_S09_DECISION_DIR=runtime/frozen-c3` (backend `_c3_decision_path` checks override first; without it `_repo_root` resolves to `worktree/output/...` stale). `run-c7.js` must stage decision JSON at BOTH `runtime/frozen-c3/` (primary) AND `runtime/output/s09/.../t00-i05-c3/` (fallback for `_repo_root`), benchmark at canonical `BENCH_REL`, fixtures from `SPRINT/t06b-c6/run1/runtime/tests/fixtures/s09_demo` prioritized over legacy `t06b-c4` paths — `demo-submit disabled` at Phase B (18:08 fail, 60s timeout on `getByTestId('demo-submit')`) was first symptom of stale fixture/decision staging, fixed by same 2-file patch + internal rerun within one hermes session.
- **Windows launcher nuance**: helpers `spawn(..., {shell:false})` stays for `python -m uvicorn` and explicit `node next/dist/bin/next start` so `C:/` paths aren't WSL-translated, but `run-c7.js` `spawnSync("npx", ["next","build"])` DOES need `shell:true` on Windows because `npx` is a `.cmd` shim — `ENOENT` without it. Don't blanket-ban `shell:true`; audit per spawn surface.
- **One-shot correction loop**: a Run1 fail inside Final (18:08) was corrected internally by the same hermes session without Manager re-dispatch — Manager observed `e2e-results/.last-run.json` flipping `failed→passed` at 18:15. Only dispatch a Manager-level fix packet when worker's own iteration leaves schema-incomplete evidence after both runs pass (this C7 case).

See `references/s09-c7-owned-restart-correction.md` for staged file list, launcher diff, lifecycle/evidence JSON before/after, and fresh run1|run2 hashes/DB sizes.

## C7-R1 reproducible build continuation (verified 2026-08-27)

Passing Chromium runs on a stale `.next` are not reproducible. C7-R1 shipped BUILD_ID-only reuse (`frontendBuiltOk()`) while `.next` baked 8888 — a fresh isolated run failed at `(không có project)`. Full recipe: `references/s09-c7-r1-reproducible-build.md`. Contract: delete the BUILD_ID-exists shortcut; invoke Next CLI via `process.execPath` + `frontend/node_modules/next/dist/bin/next` `shell:false` (Playwright via `frontend/node_modules/playwright/cli.js`, no `npx`, no `shell:true`); build with explicit `NEXT_PUBLIC_API_URL=http://localhost:8201` + frozen benchmark rel/SHA; scan `.next/server|static` (exclude dev/cache/maps) requiring 8201+bench present, 8888/8099 absent; emit `frontend-build-manifest.json` (BUILD_ID, counts, chunkHashes); no `.next` mutation after Run1; runs stage ONLY from one immutable fixture bundle (`manifest.json` + `manifest.sha256`), recording source/dest manifest SHAs; parameterized `r1/run1|run2` roots.
See references/s09-c7-r2-build-integrity.md for manifest validator, explicit-root guards, and negative-control evidence.
See references/s09-c7-r2-manager-audit.md for Manager post-exit J1/registry/DB audit and negative-control repro after R2 x2 (blank EOF, inputHashes, state column trap).

Live execution trap (verified 2026-08-27 C7-R1 19:43 → 20:10): worker `20260824_131423_423e42` patched `next.config.ts` + launcher + fixture bundle (21 files `6639dd87`) then exited after a soft 52-pass backend probe (`pytest reskin_config+reskin_migration+renderer_router` 28s) without running FINAL build-first x2 — `frontendBuiltOk()` removal and explicit `node+next` shell:false were on disk but `t06b-c7/r1/run1|run2` had not yet been created. Manager must NOT treat any early `exit 0` after patch as terminal: verify FINAL x2 existence on disk (`r1/run1/playwright-stdout.log` + `r1/run2/playwright-stdout.log` + `r1/frontend-build-manifest.json` `atcxDWpHgTN3FmPD3oNt0` 182 chunks `8201×4` `bench×2` `forbid 0`) before closing. Second resume `prompt-t06b-c7-r1-continue.txt` (same owner, same `meta`/`max`/TTFB900) completed PREP re-verify + build reuse check (mtime 19:37 < run stdout) + sequential `node run-c7.js --run run1` 35.1s + `run2` 34.0s + retained gates (J1 13/13, TSC 0, ESLint 0 via `frontend` cwd `eslint.config.mjs`, `git diff --check 0`, fixture verify, ports/TIME_WAIT only). TTFB 900s on 150k-token context masks progress (log shows `bash: no job control` until 20:10) — Manager independently audited lifecycle 18 keys / evidence 21 keys, `initial≠replacement`, `listenerBefore==initial`, `portReleased all true`, DB distinct `068b47c3` vs `217bd12a` while sharing exact BUILD_ID, proving the one-shot loop closed in one continuation without opening C8.

## C7-R2 build integrity & config guard (verified 2026-08-27 R1 review F1-F4)

Full recipe: `references/s09-c7-r2-build-integrity.md`.

- F1: `next.config.ts` keeps normal 8888 fallback; `8201` is test-only build-time injection. R1 violated write-set with an `8201` fallback — grep the fallback before dispatch.
- F2 7-check fail-closed validator before any `spawnSync`: manifest+.sha256 match; exit 0 + env contract 8201 + bench rel/SHA; BUILD_ID equal; exact file set; per-file SHA; fresh scan counts with `8201+bench` in, `8888/8099` out; inputHashes match. `--build-only` rebuilds via `process.execPath` + Next CLI `shell:false`; `--run` never rebuilds; add `--verify-build-only` + bad-hash negative control.
- F3 roots: `--run-label/--runtime-root/--output-root` absolute, distinct, fresh, task-owned; reject MAIN/repo-root/home; never `rm -rf` prior evidence; stage only from the verified fixture bundle.
- F4: fix blank-EOF before terminal; never claim `diff --check 0` without running it on the current tree.

## Long-gap resume, worker context-exhaustion, hard quotas (verified 2026-10-07, LONG01)

Raw extracts: `references/long01-long-gap-context-exhaustion.md`.

- **Recon before ANY resume after a gap — the project moves faster than chat memory.** Order: `date`; worktree `git log --oneline -15` (expect unknown commits); newest `docs/pm/prompts/*` + `reviews/*` by mtime; top "Current execution" of `CODEX_PM_HANDOFF.md`; active RUN's `manager/registry/SESSION_REGISTRY.json` + `DISPATCH_LEDGER.jsonl` tail. The sprint you left may be CLOSED with a different task active.
- **`exit_code: 0, timed_out: false` + log tail "Max compression attempts (3) reached / Context length exceeded" = invocation limit, NOT completion.** Confirm the old writer is terminal (its own `Resume this session with:` line proves exit), then resume the SAME owner with a compact continuation packet built from its own `RESUME_STATE.md`/checkpoint — never re-feed history, never restart the run.
- **PID-alive claims need identity checks.** `exact_child_pids_alive: [4632], worker_alive_exact: true` was FALSE — the PID was `conhost.exe`. Verify name + command line; trust log fields (`log_grew`, `sec_since_growth`, `stall_8min`) for liveness.
- **Hard quota (429 RATE_LIMITED + reset time) = BLOCKER report, not a retry loop; never silently switch model.** Rules §7 carves quota/auth/config out of infinite retry. Keep checkpoint; report exact payload + reset; route changes come from the user's newest directive.
- **Context-overflow 400 is arithmetic:** messages + completion budget > model max (917,958 + 131,072 > 1,048,576). Shrink payload/patches or lower the per-task output ceiling; never rewrite global router/model config.
- Git-bash Windows checks: single-quoted `powershell -NoProfile -Command '<PS>'` for `Get-CimInstance` (bash eats `$_` if double-quoted); `curl -s http://127.0.0.1:8188/queue` for ComfyUI; `ps aux`/`ps -o` do NOT exist here.
See `references/s10-full-apply-dag.md` for S10 8-owner DAG, write scopes, model/heartbeat contract and date-anchored ETA wall table (parallel T01A||T01B, serialized T01C..T04C).
See `references/s10-t04a-continuation.md` for the T01A→T04A continuation (J1–J5 verified 124×2, W1→W5 DAG+traps+ETAs; gateway 524 retry same-session, alembic/pytest/heredoc traps intra-detail).
See `references/s10-live-w1-eta-and-gateway-524.md` for the T01B 26×2 green + 524 `RUNNING_RETRY_WAIT`/5' resume loop and ETA wall contract that fired the same session.
See `references/s10-dispatch-pitfalls.md` for S10 W1 verified pitfalls: Vietnamese prompt heredoc EOF break (use file-write not heredoc), shell `&` blocked by terminal (use background=true only), and mid-turn go+ETA co-occurrence rule.
See `references/s10-j1-gate-verification.md` for S10 J1 verified 47×2 close (alembic CWD trap, pytest invocation trap, prompt-file heredoc trap, and dispatch retry that survived a 524/Retry-Wait).
See `references/s10-w1-eta-gateway-and-j1-traps.md` for S10 W1 heartbeat/ETA contract, 524 same-session 5' resume, Vietnamese heredoc + shell-`&` traps, and T01B planner purity proof.
See `references/s10-t01c-handler-and-acceptance-routing.md` for S10 T01C handler registration miss (job_service wiring not in allowlist), T04C `BLOCKED_WITH_FINDINGS→` exact-owner correction → same-session resume loop, and T04B P2 docs-only carry-forward at J6.
See `references/s10-t04c-job-enqueue-and-parse-pitfalls.md` for S10 T04C job enqueue swallow + SQLite busy (commit-before-enqueue + narrow IntegrityError-only swallow) and harness `{projects:[]}`/`{videos:[]}` shape mismatch — the P0 that blocked 2× Chromium Run1 after the handler fix.
See `references/s10-c1-real-full-apply-correction.md` for S10 C0 Codex CHANGES_REQUESTED (122+2, null SHA/size, fabricated .bin, forgeable structural gate) → 6-correction serialized DAG `T02-C1→T01C-C3→T03-C1→T04A-C1→T04B-C1→T04C-C1` with real renderer executor, commit-before-enqueue, strict restart/provenance and server-derived metrics.
See `references/s10-c1-iteration-network-route.md` for S10-C1 iteration-limit twin continuations (T01C-C3 hit `--max-turns` twice before J2), `Network connection lost` ×3 retry loop (RUNNING_RETRY_WAIT 5 min, same owner), controlled_redraw route gap (2/38), stitch 200→100 dedup + tampered quarantine fix (15+2→17×2).
See `references/vietnamese-eta-typo-and-report-truncation.md` for `essti`/`up darte`/`baoh` typo ETA variants, `sao lại dừng r` liveness typo, and S10 exit Report truncated heredoc fix (use file-write, not shell heredoc, for JSON-heavy reports).
See `references/s10-c3-reality-exit-correction.md` for S10-C3 Reality Exit Correction (T03 real T02 renderer + Windows path-budget, T04A measured fail-closed gate, T01C 9-file mypy, T04C 2× current-build vertical runs, serial DAG `T03→T04A→T01C→T04C`).
See `references/s10-c3-reality-correction.md` for the S10 C3 reliability ledger (routing 402 vs ping, transient retry, quoting, T03 fabric/path, T04A fail-closed).
See `references/s10-c3-t03-real-renderer-and-path-budget.md` for the verified T03-C3 execution (delete 637-696 fabric, `S10MultiRoleService.execute_role_chunk` with pinned identities + `affected_region` perturbation, `ManagedRoot.atomic_write_bytes` bounded `s10_recompute/{run8}/{corr8}/c_XXXX.mp4` path-budget, 4 instrumented tests, nested-root sweeps).
See `references/s10-c3-c3-continuation-lessons.md` for the C3 continuation traps hit live (inline `-z` quoting EXIT 2, `segment_motion.transform_json` NOT NULL swallowed by `except: pass` → BLOCKED, nine-file mypy ownership carry-forward 72→0→11, and report heredoc truncation vs `write_file`).
See `references/s10-c3-t04c-vertical-harness.md` for the T04C strict vertical run (8/8 fabric→server-truth fixes, `replace(/\n/g` SyntaxError gate, 150s lease fencing `_force_requeue.py`, `stage_c4.py` fail-closed staging, BUILD_ID KIWvay6FvLdiWmVFduSMG, `node --check` + `playwright --list` harness gates).
See `references/s10-c3-lease-stage-syntax.md` for the C3 lease CHECK clamp (`expires_at >= acquired_at` → `max(acquired, now-1s)`), `stage_c4.py` helper, reconciler `INPUT_CHANGED` fencing bypass, `replace(/\n/g` split SyntaxError gate, and 9-file mypy ownership carry-forward (T01C 72→0, T03/T04A 11 carry-forward).
See `references/s10-c3-t04c-runtime-traps.md` for T04C isolated runtime traps (managed_root `/artifacts` mismatch, recompute `session_factory` swallowed `except: pass`, lease `max(acquired,now-1s)` + `grace=0`, perturbation `%6+1` delta 0, decode `PYTHONPATH`).
See `references/s10-c3-structural-fallback.md` for the structural fallback fix — empty `segments=0` seeder → 10× MISSING → server-derived `source_cut=[50]` + trajectory/scale/rotation/contact from chunk evidence (gate was fail-closed correct, harness seeder incomplete).
See `references/s10-c3-exit-gates.md` for the C3 EXIT 9-gate recipe — `170×2` fresh nested (`MOTIONFORGE_DATABASE_URL UNSET`, `-p no:cacheprovider`), J1-v4 13/13, ruff F, mypy 15 fair (T01C 0), diff 0, alembic `a10b11c12d3e`, build `KIWvay...` 7/7, ports free, DB truth run1+run2.
See `references/s10-c4-authority-fence-preflight.md` for the C4 authority-fence correction (full rules-load order, source-sweep baseline before dispatch proving the reviewed defective state, route probe matrix `-m deepseek-v4-flash` FAIL vs `-m ocg/deepseek-v4-flash` pong, `.ps1` process-audit file pattern, J1-v4 re-hash via packaged script).
See `references/s10-c4-t03-correction-semantics.md` for the T03-C4 continuation (1-line `Codex response remained incomplete` signature, mtime-proof of landed edits before 5-min resume, honest-RUNNING→immediate-R3 rule, banned-perturb reseed trap, J1 179×2 independent gate, anti-"fair"-waiver reconciliation).
See `references/s10-c4-exit-gates-and-eslint-scope.md` for the full C4/C4A exit-gate sequence (206×2 final counts, ESLint scope-precedent vs pre-existing-error mtime classification incl. `page.tsx:90` carry-forward P2, basetemp-length sensitivity on >260 path tests, SUPERSEDE pattern for false prior claims, BUILD_ID change on rebuild = expected, truncated-worker-log → disk-evidence audit, porcelain +1 on coordination appends).
See `references/s10-c4a-t04a-longpath-reader-fix.md` for the long-path CONSUMER-READ defect (gate `is_file()` on plain path vs producer `_lp()` extended path — `RENDERED_FILE_MISSING` unconditional on deep roots; wrap `_win_long_path` ONCE at `abs_path`, mkdir WinError-123 trap at ≥24 nesting, regression must emulate producer write-through-extended form).
