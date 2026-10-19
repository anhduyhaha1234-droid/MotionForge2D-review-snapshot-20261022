# Worker liveness monitoring + pre-staging (manager-side)

How to answer "is the dispatched CLI worker actually running OK?" and how to use
reasoning gaps productively. Context: `hermes -z ... --resume <owner> -m <model> --yolo`
background dispatch; agent.log does NOT capture CLI `-z` sessions (only desktop
sessions appear there) — grepping agent.log for the worker session id returns nothing
and is NOT evidence of death.

## Why dispatch.log stays 0 bytes (normal)

`hermes -z` buffers stdout and prints only the final result at exit. A 0-byte
dispatch.log for 1-2+ hours is EXPECTED for a reasoning-heavy worker, not a hang
signal. Do not kill/re-dispatch because of it.

## Liveness ladder (check in this order, cheapest first)

1. **Write-set probe**: `find <allowlist files> -newermt "<dispatch time>"` — any
   mtime hit = worker is writing (strongest signal).
2. **Process tree**: `wmic process where "ParentProcessId=<bash pid>"` — expect
   `bash → bash → hermes.exe → python.exe` chain still alive (hermes.exe is a shim;
   python.exe does the work).
3. **Router TCP probe**: `netstat -ano | grep "<python pid>"` — an ESTABLISHED
   connection to the LLM router port (e.g. 127.0.0.1:20128) means a call is in
   flight RIGHT NOW. Connection open/closing cycles are normal between turns;
   CPU time (`UserModeTime`) should creep up between polls.
4. **Read-only pytest smoke**: `pytest <files> --collect-only -q` — proves the
   import graph is still healthy while the worker churns (0 collection errors).
   Collect-only is safe mid-flight; a FULL pytest run is NOT (worker edits those
   very files — serialized DAG forbids running the suite the worker owns).

## Diagnosis table

| Signal | Meaning |
|---|---|
| log 0 bytes + tree alive + TCP established | healthy, mid-reasoning/API call |
| log 0 bytes + tree alive + no TCP + CPU flat | between turns or long reasoning; recheck in 15-30 min before acting |
| tree gone + notify never fired | dispatch failed early; check dispatch.log for shell errors (e.g. bad flag order — `-m` must come AFTER `-z "<prompt>"`; `hermes chat -z` is INVALID — `-z` is a top-level flag, use `hermes -z "..." -m ...`; `--max-turns` does not exist on hermes CLI) |
| worker writing files steadily | healthy; DON'T run gates until it lands |

## Pre-staging during reasoning gaps (serialized DAG compliance)

While the worker reasons (no write-set changes yet), the manager can safely prepare
NON-conflicting artifacts in manager-owned output dirs:

- **Draft the next node's resume prompt** (worker T04B/T04C prompts) — ready to
  dispatch the moment the previous node lands.
- **Write the gate script** for the upcoming join gate (sub-checks with `.code`
  marker files + logs, `git status --porcelain` snapshot). Validate mechanics
  early: `bash -n script.sh` for syntax; run only the read-only sub-checks
  (broad-except sweep, OpenAPI duplicate scan) to prove they work — record their
  BASELINE output now so post-fix deltas are meaningful (e.g. broad-except sweep
  hits 17 pre-fix → expect 0 post-fix).
- **Build skip decision**: compare the build manifest's `inputHashes` against live
  files to pre-decide J6-BUILD. PITFALL: manifest input paths are relative to
  `frontend/`, not the worktree root — prefix them or everything reads MISSING.
  All-SAME ⇒ skip rebuild with a hash-equality proof file; any CHANGED ⇒ rebuild.

### PREP-R artifacts MUST land in the same turn as the probe — stall detection (S10-C6H, 2026-09-02)

The Rebasing manager continuation can burn many turns "building evidence" and
still produce zero disk artifacts. Codex verdict for that stall:
`AUTHORIZED_TO_DISPATCH / PREP_R_STALLED / NOT_APPROVED` — "báo cáo không artifact
= KHÔNG tiến độ". The manager produced an ETA table and a progress report twice
while `output/s10/c6h/` stayed EMPTY. Rules (apply to every evidence-build phase):

1. **Persist in the SAME turn you compute**: `AUTHORITY_SOURCE_LEDGER.md/json`
   (per-test provenance: msg_ids+sessions+byte counts+SHAs) and
   `RETAINED_<N>_MATRIX.md/json` (N concrete rows: node, evidence source,
   setup/action/expected, durable-state invariant, disposition). A turn that
   ends with only a plan and no artifact = NO_PROGRESS by definition.
2. **Progress reports must cite artifact path + SHA or command exit code** — never
   "đang tiếp tục" without one. If no new evidence, say `NO_PROGRESS` flatly.
3. **Guard the dispatch**: `write_set_guard.py capture` (route + main test +
   critical dirty/untracked files) BEFORE dispatch; `verify` after every writer
   stop. Persist `write_set_manifest.json` + snapshots under
   `output/s10/c6h/manager/guard/`.
4. **Registry BEFORE first write**: append the worker session id to
   `docs/pm/sessions/S10-SESSION_REGISTRY.md` before the worker's first tool
   write (rules §5.8). Query the DB for the new session — the CLI session id is
   NOT printed on dispatch; read the first `user` message of the new session to
   confirm it carries the dispatch prompt. DB QUIRKS (S10-C6H, 2026-09-02,
   verified against `PRAGMA table_info(sessions)`):
   - the sessions table has NO `session_id` column — it is `id`. A naive
     `WHERE session_id=...` fails `no such column: session_id`.
   - **`source='cli'` is NOT a reliable filter.** The C15-A dispatch
     (`hermes -z ... -m comboBAI`) registered with `source='desktop'` because
     the desktop daemon hosts the CLI runner. Filter instead by
     `WHERE started_at > <dispatch_ts> ORDER BY rowid DESC` and identify the
     new session by its first `user` message containing the dispatch prompt
     (compare the leading `# S10-...` title line).
   - Confirm the model too: `model='comboBAI'` + `billing_base_url` shows the
     actual upstream router once the session row exists.
5. **Probe dispatches with `hermes -z "..."` NOT `hermes chat -z "..."`** — `-z`
   is a top-level flag; `hermes chat -z` errors `unrecognized arguments` (exit 0!
   the `| tail` pipeline masks the error code — check `c15a_dispatch.log` and the
   `EXIT:` marker, not the pipeline's status).
6. **Reconcile with arithmetic**: current textual defs − obsolete − duplicate =
   target (64 − 1 − 1 = 62). Static assert counts in code; never hand-wave.

## Anti-patterns

- Running the full focused suite while the worker is mid-flight on those files —
  invalidates the result (worker churns code) and violates DAG serialization.
- Treating 0-byte dispatch.log or agent.log silence as worker death.
- Re-dispatching a new session instead of polling the exact background process
  (`process action=poll`) — owner discipline applies to monitoring too.

## No-final-response death → partial-landing recovery (S10-C6B, 2026-08-31)

A resumed owner session on a long context can die with `WORKER_EXIT=1` and
`dispatch.log: hermes -z: no final response was produced; treating the run as
failed.` (context-compression kill pattern). This is NOT a total loss:

1. **Verify partial landing yourself** (never trust the silence): grep for the
   new symbol (e.g. `grep -n cancel_run_atomic <files>`), compare write-set
   mtimes against dispatch time, read the worker's LOG.md tail for its own
   design record. Classify: what landed / what's missing.
2. **Resume the SAME exact owner session** (iteration limit is not a blocker)
   with a SHORT turn-2 continuation prompt — do NOT re-send the full prompt;
   state landed-vs-missing as verified by you, the remaining ordered steps, and
   the guards. A short prompt avoids re-triggering the compression kill and
   reaches work immediately.
3. **Instruct incremental LOG appends** (1-3 lines after each work group) so a
   later death loses nothing and the next continuation prompt writes itself.
4. Re-arm monitoring on the NEW pid (old heartbeat cron references the dead
   one) and append the result to the session registry.
5. Collect-only smoke after death is safe and useful: `pytest --collect-only -q`
proves the import graph survived the partial edit before turn 2 starts.

### Exit-2 empty-log variant (S10-C6C, 2026-09-01)

`WORKER_EXIT=2` with a ~14-byte dispatch.log (only the exit marker — no "no final
response" message, no traceback) is a SECOND death mode on long owner sessions.
It hit twice in a row on the same resume in C6C: T1 landed zero bytes; T2 still
landed the prompt-reading + design group into LOG.md despite its own empty log.
Recovery:

1. Audit landed bytes FIRST (write-set mtimes vs dispatch time, LOG.md/REPORT
   tail, `git status --porcelain` count vs baseline). Empty log ≠ zero progress.
2. Prove the owner session + model route still resolve with a liveness probe in
   RESUME form (`hermes --resume <owner> -z "reply exactly: RESUME_ALIVE_OK …"
   -m <model> --provider <provider>` — seconds-cheap, doubles as a model-route
   re-check after the failure).
3. Wait the retry-policy minimum (≥5 min per Rules §3), then resume the SAME
   exact owner with a SHORT continuation prompt (verified landed-vs-missing +
   ordered remaining steps + per-group LOG-append instruction).
4. Two consecutive exit-2s are a turn-chaining pattern, not a blocker — treat
   them like compression-kill turns. Only classify BLOCKED when the landed-bytes
   audit shows the session is corrupt or the resume-form route probe fails.

### Clean-exit bookkeeping gap: EXIT 0 + LLM-401 log tail + LOG/REPORT append never landed (S10-C6E, 2026-09-01)

THIRD variant, and the sneakiest: `WORKER_EXIT=0`, the worker's own
evidence.md is COMPLETE (all gates green — focused ×2 fresh roots, ruff/mypy/
alembic/diff-check, SHA before/after table, porcelain accounting) and even
contains the sentence "Final terminal line: `STATUS: TASK_SUBMITTED`" — yet
the LOG.md/REPORT.md node append, the registry entry, and the real terminal
STATUS line NEVER landed. C12-T3 case: evidence.md mtime 21:18:38, but
LOG.md/REPORT.md both mtime 18:45 (pre-dispatch), `grep -c C12 LOG.md` = 0,
registry last line = the PREVIOUS turn (T2). The dispatch log's final line
is `HTTP 401 ... 鉴权服务请求失败 (context deadline exceeded)` — the worker's
LAST LLM turn died on an auth-service timeout AFTER every artifact except the
bookkeeping had been written, and the CLI still exited 0.

Rules:

1. **A `STATUS:` claim inside evidence.md is a self-report, not an append.**
   Verify the terminal line in the ACTUAL manager artifacts:
   `grep "STATUS:" LOG.md REPORT.md`, `tail -1 <registry>`, and compare
   LOG/REPORT mtimes against dispatch time. If mtimes predate dispatch or
   grep finds nothing, the node is NOT submitted no matter what evidence.md
   narrates — never propagate a "TASK_SUBMITTED" derived from reading the
   claim in evidence.md alone.
2. **Read the TAIL of dispatch.log, not just `WORKER_EXIT=0`.** An
   `HTTP 401/5xx`/auth-timeout line as the last line before the exit marker
   is the tell that the final turn failed after the work completed
   (evidence.md mtime < dispatch-log error time). Exit 0 does not mean the
   final response cleanly delivered.
3. **Recovery = SHORT resume of the exact owner (same model), bookkeeping
   ONLY**: append LOG.md + REPORT.md node section + registry line + final
   `STATUS:` terminal line. No code, no tests — the landed evidence is
   already green; re-running gates is pure waste. If the 401 is infra
   (auth-service timeout), retry once after the timeout window; if it
   recurs, escalate per the model-route probe rather than re-running the
   node. This sits next to the "clean exit with remaining work" pattern:
   same short-continuation shape, different trigger (missing bookkeeping,
   not missing implementation).

### Clean exit with remaining work is NORMAL — turn-scoped node completion

A turn-2+ continuation on a long owner session often ends EXIT 0 WITHOUT
finishing the node. Expect a T1→T2→T3 sequence per node (death-recovery →
clean partial → shakeout/validation/submission) rather than one dispatch doing
everything — do not treat "exit 0 but node incomplete" as a failure. The clean
exit's final response is an asset:

1. **Mine it for the next resume plan**: comboBAI workers end with a structured
   remaining-work list ("Chưa làm (Manager resume ngay được)") including their
   own risk notes (e.g. which new tests have never run, which asserts may need
   fixing). Convert it verbatim into the next `prompt_tN.txt` — the worker
   already wrote its own handoff.
2. Name per-turn artifacts (`prompt_t2.txt`, `dispatch-t2.log`, …) and append a
   one-line registry entry per turn with the new proc id — the registry becomes
   the node's turn ledger.
3. Keep every continuation prompt SHORT (verified landed-vs-missing + ordered
   remaining steps + guards). The same shape that dodges the compression kill
   also produces the clean exit + self-generated handoff.

### Heartbeat cron arming pitfall

`cronjob create schedule='10m'` is silently ONE-SHOT (`schedule: "once in 10m"`,
`repeat: once`, `deliver: local`) and saves output locally without chat delivery;
it also disappears after firing, so a later `cronjob update <id>` fails with
"not found". Correct shape: `schedule='*/10 * * * *'` + `repeat=N` (cap it,
e.g. 12 = 2h of coverage) + `deliver='origin'`. Run `cronjob list` first
whenever an id stops resolving.

**Cron model silently inherits the global default.** A cron job without an
explicit model runs on `config.yaml` `model.default` (here that was `meta`/muse
— the user rejected it for heartbeats: "đổi model heartbeat sang comboBAI luôn,
đừng dùng meta nữa"). The `cronjob` TOOL has NO model field; use the CLI:
`hermes cron edit <job_id> --model <exact-id> --provider <provider>` (verify
afterwards with `cronjob list` — `model`/`provider` must show the override).
When a mid-sprint user model override lands, apply it to EVERYTHING in the
same turn — worker dispatches via `-m`, heartbeat/monitor crons via
`--model`, plus memory + registry — so no automation silently keeps running
the excluded model. See also `references/model-route-override-probe.md`.

**Armed cron can VANISH between turns — verify both views after every arming
action (S10-C6H, 2026-09-02).** A heartbeat created via the `cronjob` tool
(`schedule='10m'`) then "fixed" with CLI `hermes cron edit <id> --schedule
'*/10 * * * *'` was GONE at the next check: `cronjob list` → `count: 0, jobs:
[]` AND `hermes cron list` → "No scheduled jobs". Do NOT trust the previous
turn's create/edit outputs — re-verify in the SAME turn you rely on it:
`cronjob list` (tool view) AND `hermes cron list` (CLI view); jobs.json
(`AppData/Local/hermes/cron/jobs.json`) shows the model pin too. Shape
verified to persist (state: scheduled, repeat: forever, next_run_at set):
create DIRECTLY with the cron EXPRESSION `schedule='*/10 * * * *'` (NOT
`'10m'` — 10m is the one-shot trap), then immediately
`hermes cron edit <id> --model <exact> --provider <provider>` + list-verify
the pin. When the tool's list shows the job but CLI shows none (or vice
versa), trust the job that also has `enabled: true, state: scheduled,
next_run_at` — and re-create, do not repair, a vanished heartbeat.

**Arming gap**: a heartbeat cron created via the `cronjob` TOOL always starts
life on the global default model (the tool has no model field), so each
re-arm during the sprint is TWO actions in the same turn: (1) `cronjob create`
(with the new pid in the prompt), (2) immediately
`hermes cron edit <job_id> --model <exact-id> --provider <provider>`. A job
edited later — or an old job whose pid died — runs beats on the wrong model
until you fix it. If an edit says "Job not found", the job expired (repeat
budget) or was one-shot; `cronjob list` first, then create v3. Cap repeat
(~9-12) so stale monitors die instead of accumulating. To re-target an ALIVE
job onto a new pid, `hermes cron edit <job_id> --prompt "<new check>"` —
no need to recreate. Two verification quirks from C6C: the cronjob TOOL's
`list` shows `model: null` even after a CLI edit pinned the model — verify
the pin via `hermes cron list` (CLI view) instead; and `repeat: forever`
jobs do NOT self-expire like the capped ones — when the sprint goes terminal,
REMOVE the heartbeat explicitly (`cronjob remove`) or it keeps ticking
silently (`deliver: local`) with a stale pid in its prompt.

## R-GATE: independent verification may overturn the worker's own classification (S10-C6H, 2026-09-02)

The worker published `STATUS: C15_A_SUBMITTED` while its own verify chain
reported **57 failed / 5 passed** — and classified the failures as
"HARNESS/AUTHORITY gap, NOT CREDIBLE_PRODUCTION_RED, **not clearable by minimal
patch**, owner: Manager R-GATE". The Manager's independent audit then produced
the exact one-hunk fix, and the classification was WRONG. Rules learned:

1. **A worker's "not clearable by minimal patch" is a hypothesis, not a gate.**
   The worker compared current seeding against its own `pre-edit/*.bak` — a
   byte-identical re-run would trivially agree, making the comparison CIRCULAR.
   The authoritative evidence was the pre-destruction **read-pages**
   (`read_pages_manifest.json`): reconstruct the seeding/helper functions from
   the line-numbered page contents (`offset`+content merge → `line -> text`
   dict) and diff against the current file. Reconstructed lines 100-104 showed
   the real `_make_client` MUST end with
   `_seed_v2_authority(factory, artifacts_root, seed, route=route)` — the
   current file omitted it and used a fabricated `checkpoint_hash` → the 57
   failures were exactly that single missing call.
2. **Cross-check the claim against a PREVIOUS GREEN RUN on the SAME route.**
   C6F's shakeout passed 82 (57 API + 25 workflow) on this exact route
   `6ADCC48A` — the seed path demonstrably worked. A "harness gap" claim that
   contradicts a prior green run of the same suite on the same route is suspect
   until the seeding diff is proven.
3. **Workers classify against their OWN dirty backup; the Manager must diff
   against the AUTHORITY source** (VSS ancestor, read-pages, patch-proven
   payloads). This is the same "verify the artifact by its own class" principle
   applied to evidence provenance, not just commands.
4. **"Owner: Manager R-GATE" hand-off is not a blocker** — it is an explicit
   escalation the Manager resolves. The combined correction packet (exactly one,
   per binding prompt) is then dispatched to the SAME fresh C15 session as a
   short continuation: state the verified finding + the evidence-backed hunk,
   no re-apply of prior patches.
5. **Read the full dispatch log tail, not just the summary table.** The
   worker's own summary table said "57 failed/5 passed, harness gap" and its
   last paragraph said "STOP — chờ Manager R-GATE" — but the detailed
   classification paragraph contained the real root cause (STORED=fc51bc6a vs
   RECOMP=c43b3884 → MATCH=False) AND the admission that the fix "needs rework
   `_make_client` seed v2 authority" — i.e. the worker knew the exact fix and
   still refused it. The Manager's job is to read that detail and turn the
   known fix into the correction packet.

## Manager gate execution (J6C pattern, 2026-08-31)

When a join gate fires, don't just re-run the worker's commands — shape them
for independent, auditable evidence:

- **Per-gate `.code` marker files**: each gate writes `<name>.code` containing
  its exit code plus a full `<name>.log`; end the script with a summary loop
  over all markers. The run is then auditable from marker files alone, and a
  heartbeat cron can report gate state by reading only the `.code` files.
- **Manager-owned risk-matrix probe**: after the focused suites, run ONLY the
  corrected/latent-risk tests as an independent execution, e.g.
  `pytest <files> -k "cancel or resume or retry" --basetemp=<fresh>`. This
  proves the race tests pass under manager invocation, not just in worker logs.
- **Route-scoped broad-except sweep**: a global "except Exception: <no raise>"
  sweep over-counts legitimate handlers (metadata fallbacks, read-only
  inherit). Scope it: map each line to its owning `def` (walk backwards for
  `def \w+`), flag swallow only inside the corrected routes
  (cancel/retry/resume). Record the PRE-FIX baseline hit count during
  pre-staging so the post-fix "0" is a meaningful delta (17 → 0 in C6B).
- **Shakeout-first order** (mirrors how the worker itself validated):
  `pytest -x -q` shakeout → focused ×2 fresh roots → risk-matrix probe →
  full suite ×1 → static gates (ruff/mypy/OpenAPI/alembic/diff-check/
  porcelain) → only then read REPORT.md. Fail fast on fallout before paying
  for the full matrix.
- The gate script must honor the SAME env constraints the worker hit: short
  pytest basetemp roots under `%TEMP%` (WinError 206 — see the motionforge-2d
  s10 reference), DB env UNSET, `-p no:cacheprovider`, and per-run distinct
  roots.
- **Canonical ruleset calibration — verify BEFORE scripting**: bare
  `ruff check` runs the full default ruleset (E501/I001/N814 → hundreds of
  pre-existing style hits on mature code; C6B saw 343) while the sprint's
  real gate is `--select F` (evidence-log naming like `ruff_F.log` is the
  tell). Read the prior gate evidence logs during pre-staging and copy the
  exact command; a wrong-ruleset `RUFF=1` is a SCRIPT false positive, not a
  product defect — re-run the canonical command manually, record both
  outputs in the verdict (J6C_VERDICT.md did), and never "fix" style errors
  the gate never gated.
- **Sweep hits: verify against the handler, not the regex**: a broad-except
  sweep can flag a legitimate nested rollback-guard — inner
  `try: session.rollback() except Exception: pass` sitting INSIDE an outer
  `except Exception:` that compensates and raises HTTPException(500). That
  is fail-closed by design, not a swallow. Route-scope the sweep first (map
  each line to its owning `def`), then manually read every hit's handler
  before declaring a defect; one LEGITIMATE hit documented in the verdict
  beats a false gate failure.
- **Live-UI acceptance failures: classify before acting**: when a full
  acceptance run fails some scenarios (16/20), sort each failure into
  harness gap vs product defect BEFORE any fix: which store does the
  failing UI call read (v1 disk store vs durable SQLite), did the scenario
  ever run live before, what does the failure screenshot show. Harness gap
  (seeder doesn't populate the legacy store) → fix global-setup with
  assertions untouched, re-run full; genuine product defect outside the
  node's scope → BLOCKED_WITH_FINDINGS. A clean-exit partial run plus the
  worker's own root-cause notes converts verbatim into `prompt_t2.txt`.

User cadence preference — UPDATED 2026-09-02, overrides the 10' rule:
heartbeat **cố định mỗi 30 phút, bắt buộc** ("heartbeat cố định mỗi 30p báo
cáo tiến độ bắt buộc"). Earlier preference was 10' while a node runs (30'
felt like stalling); the LATEST instruction wins — the reference says 30'
fixed, plus instant notify on node completion/blocker, plus any "how's it
going" gets a lead-with-status reply + ETA table with a date anchor. The
user decides the heartbeat model too — when they name a model ("đổi model
heartbeat sang comboBAI luôn, đừng dùng meta nữa"), apply it to the cron
jobs AND keep it on every re-arm: see the two-action arming pattern above.

## Desktop-session cron delivery caveat**: on the desktop app, a
`deliver='origin'` cron tick runs silently — output is saved
(`cronjob list` shows it) but nothing appears in chat, so the user may
perceive the whole heartbeat as stalled ("thấy hay dừng lắm"). When the
user asks about liveness, don't argue from tick counts: run the live
checks yourself (process tree, write-set mtime, evidence-dir freshness)
and answer with REAL state. When heartbeats must be visible in chat,
recreate the job on a gateway-connected platform
(`deliver='telegram'`/`'all'`); when the user pings between ticks, a
manual status report is the honest fallback.

**Every desktop session — including cron AND the active chat — has
`chat_id=None` (S10-C6H, 2026-09-02).** Proof path: `sessions` table
`chat_id` column is NULL on ALL desktop/cron sessions,
`delivery_obligations` is EMPTY, `gateway_routing` has 0 rows, `deliver`
resolve fails, and `origin: None`. `hermes gateway` is a
Telegram/Discord background service — it is NOT the mechanism that
displays cron results in the desktop app. Therefore a cron heartbeat
FIRING (fires tracked in `sessions`: `cron_<jobid>_<ts>` rows, status ok)
is NOT proof of delivery. Do not burn cycles debugging cron/gateway in
the critical path; the honest fallback is the detector-of-record: run a
`terminal(background=true)` heartbeat loop (writes a status file the
manager can read; shows a live terminal tab in the desktop app) and keep
the cron only as a read-only side channel. Any "no delivery" complaint
gets answered with REAL state from live checks, not tick counts.

## Build-skip decision is a PRE-STAGE HYPOTHESIS — re-verify at gate time (S10-C6B, 2026-09-01)

Hash-equality proven SAME at pre-stage (17:30) is NOT a gate-time fact: the
live-UI node then modified production frontend bytes (`api.ts`,
`apply/page.tsx`, `AppNav`, `projects/[id]/page.tsx`) and the skip shortcut
became false. The skip decision must be RE-CHECKED when the gate fires:

- Fast tell: `git status --porcelain | grep -iE "frontend"` — any modified
  production frontend file ⇒ hash-equality is dead, rebuild for real. Do not
  paper-gate on a stale snapshot.
- Rebuild flow: `node output/s10/run-s10.js --build-only` (prints the new
  BUILD_ID) then `node output/s10/run-s10.js --verify-build-only` (7/7
  validator), both appended to ONE log under a manager evidence dir.
- PLUMBING PITFALL (hit twice this sprint): `mkdir -p <log dir>` BEFORE the
  `>` redirect — bash never creates the redirect target's directory, and a
  missing dir fails the command instantly with zero work done
  (`rebuild.log: No such file or directory`, BUILD_EXIT=1). Also in main
  memory; it belongs here because gate scripts are where it bites.
- Patch the DOWNSTREAM node's pre-staged resume prompt with the new BUILD_ID
  before dispatching it — a stale BUILD_ID reference sends the worker at the
  invalidated build (old prompt said `cLDP…`; live build became `tAah…`).
- Verify hashes by PARSING the snapshot file (split its actual format —
  `STATUS path hash@snapshot hash@recompute`), never by hand-copying hashes
  into a verification dict: hand-typed wrong values produced false DIFFs and
  nearly a wrong invalidate/skip conclusion.

## Parallel manager execution — disjoint write-sets only (S10-C6B)

A docs-only worker turn (append-only LOG/REPORT under `docs/pm/`, no
code/build files) leaves the code+build tree free: the manager may run the
production rebuild or read-only gates in the SAME window (C6B ran T04B-T3
docs concurrently with the rebuild without conflict). Confirm the turn's
scope from the dispatch prompt you sent before relying on the disjointness;
never parallel-run anything touching the worker's allowlist.

## ETA-drift honesty (user cadence, 2026-09-01)

When the user calls out slipping deadlines ("sao càng ngày càng xa deadline
thế"), answer with REAL accounting: per-node planned-vs-actual table plus the
named causes (worker death turn, first-live-run defects found, reasoning-max
model latency per turn), OWN the forecast error (ETA set per single-turn
nodes with no contingency), then apply compensating cuts WITH justification
(paper gates where the evidence already exists, pre-staged prompts, same-turn
node transitions) instead of silently re-baselining. Keep every ETA anchored
to a fresh `date`, and warn immediately when a new risk appears rather than
letting the ETA drift quietly.

## Mid-flight EXIT pre-evidence + suite-currency proof (S10-C6B, 2026-09-01)

When the user pushes for speed ("có chạy cái gì song song được thì chạy đi"),
compress the EXIT window while the LAST worker still runs — read-only / no-DB
actions only:

- **Pre-run STATIC gates now**: ruff/mypy/alembic/OpenAPI-dup/J1-v4/diff-check
  touch no DB and no ports — safe even while e2e verticals run. EXIT then
  re-checks only worker-dependent items (evidence inventory, port release,
  porcelain delta, write-set, model ledger).
- **Full pytest stays FORBIDDEN mid-flight** (worker owns those files). When
  asked to "verify now" anyway, prove suite CURRENCY by forensics instead of
  re-running:
  1. `pytest <files> --collect-only -q` — import graph healthy, 0 errors.
  2. `git status --porcelain | grep '\.py$'` + mtimes of every changed .py ≤
     the timestamp of the last full-suite green run ⇒ that result is still the
     CURRENT state; no re-run needed. Record the green-run time as the
     suite-currency anchor when the gate runs.
  3. Gate scripts live under gitignored `output/` as plain bash — they cannot
     enter pytest's import graph; state that in the evidence, don't argue it.
- **Pre-stage the EXIT gate script** (`bash -n` validated) so post-landing
  execution is one command, not a authoring session.

## Verify the artifact by its own class, not the nearest pytest command (C6C)

When a system notification fires mid-flight ("worker changed file X — verify
it"), match the verification to the artifact TYPE before running anything:
bash scripts → `bash -n` (never `pytest <script>`); Python evidence scripts →
`py_compile` + `pytest --collect-only` (a full repro run mid-flight violates
the serialized DAG when the worker owns the same files); markdown/registry
appends → eyeball the tail. Running pytest against a bash script "to verify"
wastes a cycle and produces a meaningless failure — and the failure-mode trap
is doubled when the notification text quotes PREP-era output (e.g.
`ORPHAN=True / FALSE_REUSED=True`): those flags are the BEFORE-fix truth by
design, not a regression signal. Read WHICH file changed and WHY it changed
(a manager-owned gate script under gitignored output/ is not a product byte)
before classifying a notification as a defect.

## Process/model scans: .ps1 file, not inline pipes (C6D, 2026-09-01)

`wmic process ... | grep ...` command strings can trip the terminal hardline
parser ("BLOCKED (hardline): command parser limit or malformed executable
payload") even for read-only scans. Use a PowerShell script file instead —
write it with write_file, run with
`powershell -ExecutionPolicy Bypass -File "C:/Users/Admin/AppData/Local/Temp/scan.ps1"`,
then delete it:

- Quoting trap: inside a single-quoted PS string a literal `'` breaks parsing
  (`Missing ')' in method call`) — use char classes without quotes, e.g.
  `'(?i)(BAI/[^\s"]+|comboBAI|glm[^\s"]*)'`, never `[^\s"']+`.
- `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '<pat>' }`
  gives PID + matched selector + truncated cmdline — perfect for proving "no
  stale GLM worker" after a user model override ("đổi hết sang X"): the scan
  must show ZERO matches for the old model and exact matches for the new one
  (hermes.exe + its python child + bash wrappers all carry `-m <model>`).
- Inline `powershell -Command` is still dangerous from bash (`$_` gets eaten);
  the -File form avoids it entirely.
- **`wmic` direct query is the quick read-only alternative** (C6F): for
  owner/pid proof, `wmic process where "processid=12036" get
  commandline,parentprocessid /format:list` prints the full bash wrapper
  including the `--resume <owner>` + prompt.txt path — no .ps1 needed, no
  shell pipes. Confirming the command line carries the current owner id is
  the ground truth that a heartbeat's WORKER_ALIVE=YES refers to the RIGHT
  worker (not a leftover bash from an old lineage).
- **Worker subdir evidence vs 0-byte dispatch log (C6F)**: a W-RED-phase
  worker writes its pytest/evidence output into a sibling dir (e.g.
  `output/s10/c6f/t01c-c13/worker-red/red_run.log`) while the top-level
  `dispatch-c13-t1.log` stays 0 bytes until exit. When the prompt says
  "read the facts", list the node dir (`ls -la`) and read the worker subdir
  logs — the tail there shows the real phase (e.g. "4 failed, 5 passed, 48
  deselected" = RED repros confirmed) even though WORKER_EXIT= has not
  landed yet. All of it stays read-only for the heartbeat agent.

## Heartbeat/scheduled cron script location (C6D, 2026-09-01)

The `cronjob` tool's `script` field rejects absolute paths: "Script path must
be relative to ~/.hermes/scripts/" (here
`C:/Users/Admin/AppData/Local/hermes/scripts/`). Copy the collector there
(`mkdir -p` first — the dir may not exist) and pass just the bare filename,
e.g. `script: "c6d_heartbeat.sh"`. A read-only heartbeat collector that only
prints facts (worker alive, log bytes/mtime, write-set mtimes vs dispatch
time, porcelain count, registry tail) is the ideal cron script: the cron
agent gets digestible data and the manager re-runs the same script manually
for a mid-tick status check. Keep the canonical copy under
`output/s10/<round>/manager/` for evidence; the copy in the scripts dir is
for the cron only.

**Path mangling in the cron command (C6D, 2026-09-01).** A cron tick that
invokes the collector as `bash C:\Users\Admin\...\c6d_heartbeat.sh` fails
with exit 127 — `/bin/bash: C:UsersAdmin...: No such file or directory` —
because the backslashes are eaten before bash sees them, even though the
file exists. Always invoke collector scripts with FORWARD slashes
(`bash "C:/Users/Admin/AppData/Local/hermes/scripts/c6d_heartbeat.sh"`),
and schedule the cron with the script field's bare filename (relative to
`~/.hermes/scripts/`). When a heartbeat tick errors this way, do NOT treat
it as missing data: re-run the script manually with the forward-slash path
and report from real output. Same rule for any Windows path interpolated
into a cron prompt or command.

**Bare filename is NOT a reliable fix — the mangling is intermittent
(S10-C6F, 2026-09-01).** The C6F job in `cron/jobs.json` has
`"script": "c6f_heartbeat.sh"` (bare name) and one tick ran OK
(`hermes cron list` → `last_status: ok`) while the NEXT tick (23:40) still
failed with the identical mangled exit 127 — the runner re-joins the
scripts dir into a `C:\Users\...`-style path on some ticks and bash strips
the backslashes. Rules for authoring/reading heartbeat crons:

- Put the EXPLICIT forward-slash invocation in the cron PROMPT too
  (`bash /c/Users/Admin/AppData/Local/hermes/scripts/<name>.sh` prints
  the facts) so the agent can self-heal the tick instead of reporting the
  runner's failure as missing data.
- Classify before declaring anything: runner-failure vs worker-death.
  Check `hermes cron list` (last_run status) and
  `AppData/Local/hermes/cron/executions.db` (per-tick status/error rows;
  `sqlite3` CLI is NOT on this box — query via
  `python -c "import sqlite3; ..."`). Intermittent exit-127 with a live
  `tasklist` PID + fresh write-set mtimes = runner cramp, worker alive.
- Full job config for a cron lives in `cron/jobs.json` (script, prompt,
  model, provider, schedule); `hermes cron show <name>` is not a command —
  use `hermes cron list` (CLI view) and jobs.json for the truth.

**Stale-PID probe → false WORKER_ALIVE=NO (C6D, 2026-09-01).** The first
C6D heartbeat script probed `tasklist | grep " 32524 "` — T1's PID — but
the manager had already dispatched T2 (PID 34276, proc_9a86043c9843) after
T1 exited 0. The tick therefore reported WORKER_ALIVE=NO while the new
worker was demonstrably alive (bash + hermes.exe, StartTime == dispatch
time, CIM commandline carrying `prompt_t2.txt`). Rules:
(a) probe by the CURRENT turn's pid — rewrite the script's pid line on
every re-dispatch, or grep the proc id from the registry tail / dispatch
prompt instead of hardcoding a pid;
(b) when a heartbeat says NO but the registry shows a newer turn
dispatched, cross-check before declaring death:
`Get-CimInstance Win32_Process -Filter 'ProcessId=<pid>' | Select -ExpandProperty CommandLine`
(proves what the worker is running) + StartTime ≈ dispatch time + write-set
mtimes newer than dispatch;
(c) a read-only cron agent may not edit the script — report the false
negative with the real evidence (CIM cmdline, mtimes, log bytes) instead
of acting on the green/red flag.
A 0-byte `> log 2>&1` redirect stays NORMAL here — T2's dispatch log was 0
bytes while it had already written shakeout r1/r2 logs and was mid-gates.

### Heartbeat-tick interpretation: collector awareness + per-turn exit attribution (S10-C6F, 2026-09-02 00:00)

A cron tick erroring exit 127 does NOT mean the worker is gone. Read-only
sequence that produced a correct `RUNNING` verdict in one pass:

1. **Read the collector script BEFORE interpreting its output.** It hardcodes
   WHICH pid it probes (`tasklist | grep " 32916 "`), WHICH log it sizes
   (`dispatch-c13-t2.log`), and which write-set files it stats. Every
   NO/0 line must be read against what it actually probes — e.g. LOG_BYTES=0
   measures only the TURN log, not the worker's subdir evidence.
2. **Attribute exit markers by TURN, not by directory.** A node dir holds
   `dispatch-c13-t1.log` (with `WORKER_EXIT=0` from the PREVIOUS turn) and
   `dispatch-c13-t2.log` (live turn, 0 bytes). Grepping the whole dir or
   tail-ing the older log falsely reads "worker done". The live turn number
   comes from the registry tail + `prompt_tN.txt` names; only the CURRENT
   turn's log decides alive/dead.
3. **Know the node's expected artifact sequence from the CURRENT prompt.**
   `tail -5 prompt_t2.txt` lists the worker's ordered remaining steps
   (shakeout×2 → static → evidence.md → LOG/REPORT append → STATUS line).
   evidence.md absent + fresh shakeout r2 mtime = mid-sequence, not stalled;
   LOG/REPORT mtimes still pre-dispatch is EXPECTED until the doc steps run —
   unchanged bookkeeping is NOT a dead signal while subdir logs grow.
4. **Probe the pid the script hardcodes against the CURRENT owner** before
   trusting WORKER_ALIVE: walk `wmic process where "ParentProcessId=<pid>"`
   and read the bash wrapper's full CommandLine — it must carry
   `--resume <current owner id>` + the current prompt_tN.txt path. An alive
   pid from an OLD lineage passing the grep is the stale-PID false positive
   above, not liveness.
5. Exit-127 tick recurring (23:40 AND 00:00) with a bare script name in
   jobs.json = the runner cramp described above, not data loss: re-run
   manually with forward slashes and report from real output; the read-only
   heartbeat agent does not edit the cron/script — it recommends the
   forward-slash invocation in the cron prompt.
