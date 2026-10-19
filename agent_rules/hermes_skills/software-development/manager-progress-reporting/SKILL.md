---
name: manager-progress-reporting
description: "Use when reporting progress and ETAs to the user."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [reporting, orchestration, eta, user-preference, vietnamese]
    related_skills: [pm-session-execution, pm-worker-orchestration, terminal-engineering-discipline]
---

# Manager Progress Reporting

How to report progress, verified results and ETAs to the user while orchestrating long
autonomous work (worker waves, sprint gates, proof runs). This is the *reporting* layer of a
manager session; the dispatch/verify mechanics live in `pm-session-execution` and
`pm-worker-orchestration`.

## Trigger

- Any turn where the user asks "how is it going" / "when will it be done" / "bao h xong het".
- Any worker exit, gate result, incident, or milestone you have just verified on disk.
- Heartbeats while a wave is active.

## 1. Language — Vietnamese (hard user preference)

- **Write the report in Vietnamese.** This user corrected an agent **twice in one session**
  ("tra loi bang ting viet di", then out-of-band "trả lơi f bằng tiếng việt cơ mà") after
  receiving a report whose headings and prose were English. An English-heavy report is a
  preference violation, not a stylistic choice.
- Keep **machine tokens verbatim** — they are identifiers the user greps for: `RULES_LOADED`,
  `PREFLIGHT_OK`, `RUNNING`, `TASK_SUBMITTED`, `SPRINT_SUBMITTED /
  MANAGER_VERIFIED_PENDING_CODEX_REVIEW`, `CHANGES_REQUESTED`, commit SHAs, branch names, file
  paths, command lines (`ruff check --select F`), metric names, verdicts (`TECHNICAL_FAIL`,
  `NOT_REVIEWED`, `PARTIAL_SCOPE`).
- Everything else — headings, table captions, explanations, risk notes — in Vietnamese.
- **Check the artifacts, not just the chat message.** The same language rule governs the management
  documents you deliver (frozen matrices, registries, trackers, packets). Measured slip: a stray CJK
  glyph (`未`) landed inside a frozen matrix document and was caught only by reading the diff after the
  edit — a repair patch and a disclosure followed. After writing or editing any delivered doc, run a
  script-range check over it and fix before the next gate:
  `python -c "import sys,re,io; t=io.open(sys.argv[1],encoding='utf-8').read(); h=[c for c in t if '\u4e00'<=c<='\u9fff' or '\u3040'<=c<='\u30ff' or '\uac00'<=c<='\ud7af']; print('CJK:',h)" <file>`
  Expect `CJK: []`. Machine tokens (`RULES_LOADED`, SHAs, paths, verdicts) stay verbatim in Latin script.

## 2. Shape, in this order

1. **Status line first** — done / running / blocked, one line, no preamble.
2. **A table of numbers you actually measured**: file counts, bytes, line counts, SHA-256
   prefixes, ports, durations, VRAM/RAM, tool-call counts. Numbers, not adjectives.
3. **What is still open / at risk**, itemised, each with its concrete blocker.
4. **ETA table anchored to a real date with the local offset** (+07 for this user), one row per
   milestone, each row carrying its measured basis (observed tools/minute, artifacts already on
   disk, bytes already fetched). State the reason for every slip and for any milestone that
   cannot be estimated yet.
5. **The next action you are taking**, so the message is not a dead end.

## 3. Provenance and honesty rules

- Separate **"I re-ran this myself"** from **the worker's self-report**; label which is which.
- Never restate a worker claim as fact. Never claim a visual/quality verdict when the route has
  no vision — mark it `NOT_REVIEWED` and name who must look.
- Report a slip or incident **in the same message where the rest looks green**; never wait for
  the next heartbeat, never quietly re-estimate, never bury it under a success table.
- Keep failures and self-disclosed defects as first-class rows (`disposition: fail` + note).
- Do not use test counts as a substitute for the deliverable (clip / artifact / hash).
- End the packet **in chat for the user**; never auto-send review/`APPROVED`/`CLOSED` onward.

## 4. Answering "when will it be done?"

Give per-task status (done / running / queued), a per-milestone ETA anchored to date + timezone,
the measured basis for each estimate, and the top 2–3 things that could push the ETA out —
named before they happen rather than admitted afterwards. Never answer with one unanchored hour.

Build the basis from the receipts you already hold, and show it in the table rows:
per-run durations for this class of lane × the runs the milestone really needs (a code round, a
closeout round, the transport for a chain), plus the measured tax of ~one flap/budget-stop per lane
(+5 min mandatory wait + one resumption window). State which rows are conditional (a fix that only
runs if an earlier gate fails) separately, so the user sees the floor and the ceiling instead of one
number. Then name the 2–3 events that would move it — that is what makes the estimate auditable.

**A re-asked ETA is answered with the DELTA, not the same table again.** Measured 2026-09-28: the
user asked "bao giờ xong" twice in one long wave. The second answer that worked opened with the
current counts (\"18/28 done + 2 running + 1 vừa đủ dependency\"), plus one line for anything that
happened since the last ETA — including an incident and its measured cost (\"sự cố hết budget turn:
worker chết không commit → phục hồi 5m46s, đã hấp thụ\") — and then re-anchored the same dates. Show
whether each incident was ABSORBED (mốc giữ nguyên) or SLIPPED (mốc đẩy + lý do); never re-serve an
unchanged table as if time had not passed, and never move an anchor date without naming the incident
that moved it. If a milestone now depends on a CHAIN you can list (\"22→23→24/26→25→27→28\"), name the
chain and its serial length — that is what makes the number auditable when asked again an hour later.

**Estimate in rounds, not in one shot.** A CLI worker caps at a bounded number of tool calls per run
(order of ~90 for `hermes -z`), so one task legitimately spans 2–3 narrow rounds. When a measured
basis implies "this needs another round", say that in the ETA row ("code round, then a closeout round
for the evidence set + commit") instead of promising the whole milestone in one window. A slip caused
by a round boundary that you could have predicted reads as a broken estimate; the same slip announced
the same slip announced as a planned round reads as competent sequencing.

**When the remaining work is a demo-delta LOOP, enumerate ROUNDS and name what each closed.** Measured
2026-09-29: an E2E demo on a frozen candidate kept surfacing exactly one seam per round (R1→F1/F2,
R2→F4, R3→F5), each fixed as its own delta and re-run. The answer to "sắp xong chưa / bao giờ xong"
that worked had three parts: (1) **closed-live list with the evidence** (which findings verified closed
on the REAL path — DB rows / server payloads, never fixtures), (2) **the remaining rounds as numbered
steps with per-step ETA** (fix round ~30-40', merge+freeze ~15', re-run demo ~40'), (3) the total with
its basis. State which finding the latest round closed and which it newly exposed — an ETA that counts
"rounds remaining" is auditable; "gần xong rồi" without the count is not. If a round closed nothing
(the fix didn't hold), say that in the same message and re-price before the user asks.

**The budget-stop tax is now measured at 4/4 — price it into the ETA as a near-certainty on long lanes,
not a tail risk.** All four of the longest tasks in the 2026-09-28 wave (~36, ~56, ~35 and ~38 min wall)
ended with `⚠ Iteration budget reached (160/160)`. Two landed BEFORE the commit (work finished but
uncommitted; recovered by resuming the SAME session with a ≤40-call finish packet in ~6 and ~3.5 min);
the other two landed AFTER the commit + evidence closure (the banner fired in the final summary turn), so
they verified like a normal exit — nothing to recover. The post-commit variant is now confirmed twice on
this delivery: check the log tail for the banner on EVERY `exit 0` BEFORE deciding anything — if commit +
evidence are on disk, verify normally and never spend a finish packet; only a pre-commit banner earns the
≤40-call finish round. **Triage by where the cap landed before quoting any
recovery cost** — 3-row occurrence table in `independent-evidence-verification` →
`references/iteration-budget-exhaustion-and-finish-packets.md` §1a. So for lanes expected to run past
~35 min, state the finish-packet round in the ETA row itself (\\\"main round + a commit-evidence closeout
round\\\") and hand the operator the reusable skeleton rather than improvising it under pressure — see
`independent-evidence-verification` → `templates/finish-packet.md` (fill the disk-state block from your own
porcelain + test measurement). An incident you predicted and reported as a planned round does not move the
anchor date; the same incident discovered late does.

**Anchor GPU-rendered milestones on a measured run, and do the arithmetic out loud.** When the
deliverable is generated video, the ETA basis is seconds-of-render per second of video from a real
run — measured 2026-09-27: a 4 s Wan Animate 2 INT8 baseline on a 12 GB card cost 2,394 s wall =
**598.58 s per output second** at 97 % VRAM peak. Put the consequence in the row ("30 min of source
≈ 300 h at this rate; a 12 s stress demo ≈ 2 h per pass") instead of an optimistic number, and mark
any milestone whose *input file is not on disk* as `BLOCKED_SOURCE` — measured: only 7 source
windows existed and no full parent MP4, so the stress demo was runnable while the full-source demo
was honestly blocked rather than silently re-scoped. Re-derive the number after every geometry /
config change (a 480×848 run at 598 s/s says nothing about the 640×368 rerun), and quote it only as
seconds of render per second of video a reviewer **accepted**. **Close the loop in the same message
where the fix lands — and attribute the delta correctly.** Measured: the post-fix rerun came in at
**38.67 s/output-s**, collapsing the pessimistic ceiling (30 min of source: ~300 h → ~19 h; 12 s
stress: ~2 h → ~8 min). Show the corrected number AND the superseded one so the revision is
auditable. **But run the cold/warm check before calling any delta a code effect:** the
598.58 → 38.67 comparison was a **cold first run vs a warm rerun** (same profile: cold 596.95 ·
warm 38.67 s/s; every warm run since clusters ~34–39 s/s at either geometry), so most of the
"15.5×" was server warm-up, not the geometry fix. A report that attributes a cold→warm delta to a
fix teaches the wrong lesson and misprices every milestone: **budget one cold run per server
restart**, price pipeline milestones at warm s/s, and only claim a code/config speedup proven by
same-config-twice-on-one-server. Cost per **accepted** second with `accepted_seconds = 0` is
`UNDEFINED` — write neither 0 nor ∞. A fixed defect that silently keeps its old ETA in the report
is the same class of error as a stale pass.

## 5. Related detail banks (owned by skill `pm-session-execution`)

- `references/worker-wave-verification-and-guard-classification.md` — turning a worker's "done"
  into verified facts (commit/lineage/allowlist/not-pushed/re-run/determinism/large-file spot
  hashing/negative controls), splitting the guard baseline into protected vs task-owned classes,
  reading liveness when the log is empty, owner lineage + dispatch ledger, stale-registry rule,
  **§6 reconciling a worker's summary against its own artifact when the two contradict each
  other** (report the artifact's verdict + a narrow evidence-integrity correction, never the
  narrative), and **§7 freeze-before-evaluate sequencing** (owner correction → byte snapshot →
  evaluator, so an intermediate artifact is never scored).
- `references/user-reporting-language-and-eta-shape.md` — the same language/shape/ETA rules in
  long form, plus dispatch safety for mutating tools.
- Wave/DAG execution mechanics (dependency transport via `git merge --no-ff` per dep, guard
  checklist incl. `python -m alembic heads` for migration heads, verify-on-lane-EXIT loop,
  `SKIPPED_NOT_NEEDED` ≠ test pass, monitor-lane lifecycle) live in skill
  `independent-evidence-verification` → `references/mf2d-phaseb-wave-execution-verify-loop.md`.

## 6. Stale process notifications are not news

A long multi-lane wave produces background-process exit notices that land **minutes after** the
process died, and the same notice can re-arrive for a lane you already analysed and re-dispatched.
In one session most of the user's turns were such replayed notices; treating them as new events
would have meant re-dispatching healthy lanes.

- **Identify before reporting.** Match the notice's command line / packet stem against your own
  dispatch ledger. If it belongs to a round already handled, open with one line saying so — "tin
  cũ, đã phân tích và resume" — then report the *current* state.
- **Never treat a replay as a new event and never re-dispatch on it.** One read-only `state.db`
  check (`ended_at`, message/tool counts, age) plus `git status --porcelain` per tree confirms
  liveness cheaply and prevents a double dispatch.
- **Resolve which session a resume actually continued — it depends on the resume MODE.** `hermes -z
  --resume <id>` mints a NEW session id, so the parent row freeze-frames the moment the resume starts
  and every in-flight lane reads as hours stale. Measured 2026-09-25: a heartbeat reported `age=341.3m`
  for a lane that was writing tool calls that same minute — one audit cycle burned on a healthy lane.
  But `hermes chat -q --resume <id>` KEEPS the same session id (measured 2026-09-27: the row grew
  196→247 messages in place, `end_reason` still null). So check before reporting any stall: if a
  lane's "age" exceeds the time since you launched it you are reading the wrong session, and if the
  same id's message count is climbing you are on the right one. Resolve parent→actual by matching the
  first user message to the packet head (one packet per lane), record the pair in the ledger/registry,
  and use those ids from then on.
- **An `exit 0` notice is not a deliverable** (see Pitfalls); an `exit 1` on a lane you killed
  yourself is the normal exit code of a terminated process, not a failure — say so plainly rather
  than letting the user read it as breakage.
- Keep a per-lane table (task · commit · what the Manager itself re-verified) so a replay can be
  answered from the table instead of from memory.
- **A lane killed by a provider flap at the finish line is not a stall — lead with what IS done.**
  Measured 2026-09-28: two consecutive finish-rounds died on 502/422 after every GPU artifact existed
  on disk; the report described the deaths first and the user answered "sao thế / làm nốt đi" — reading
  it as no progress. Correct shape: open with the on-disk counts (runs, clips, assembly with sha), say
  explicitly "work is complete, only report/ledger docs are pending", then state the immediate relaunch
  (same session, small docs-only packet) — and do the relaunch BEFORE reporting, so the message is a
  status, not a question. Reserve the word "lỗi" for things that block the deliverable.
- **Monitor lanes are frozen at process start, so a changed lane set needs a NEW monitor process.**
  A monitor holds a hardcoded `LANES = {task: session_id}` read at import; editing the file does not
  affect the running instance. When lanes finish and new ones start, copy the script to a new name
  (new log file) and launch fresh; old instances keep printing the finished lanes and fire
  `STALL_AUDIT` on them — a stall flag is only news for a lane that is still supposed to be running.

## 7. Disclose the Manager's own errors as first-class rows

When your own final gate catches **your** defect — a corrupted management document, a wrong
`--resume` pairing, a ledger row pointing at a receipt that was never written — put it in the
report as its own item, named, with the fix and the check that now prevents it. Green tables with
the Manager's mistakes omitted read as concealment; this user explicitly values the error being
owned ("hai lỗi của chính tôi — đã khai, không giấu"). Same rule for a wrong claim you made about
a worker: retract it in the message where the corrected measurement appears.

## 8. Two timing/authority figures a reviewer will catch

Both of these were raised as formal findings against a Manager packet (2026-09-24, findings NR10), so treat
them as report-shape rules, not style nits.

**Aggregate worker duration is NOT elapsed program wall time.** A wave runs N lanes in parallel; summing
their per-run durations measures *capacity spent*, and it will exceed the elapsed window by roughly the lane
count. Report both, labelled, never one standing in for the other:

- *aggregate worker time* = Σ(per-dispatch durations) — label it explicitly as aggregate;
- *elapsed program wall* = last finish − first start, including the final continuation runs.

And finish the accounting: the last continuation of a lane (the resume after a flap, the *finish* run, the
final transport round) belongs in the timing/receipt table. A total that stops at the "main" runs of each lane
understates elapsed time and silently drops the receipts a reviewer will count.

**Do not cite an approval gate the current prompt already granted.** Writing "awaiting Codex approval for
X" / "waiting for the freeze before starting Y" when the binding prompt already authorized X/Y is an
*invented dependency*: it idles real work and makes the packet look blocked for no reason. Before any
blocker/dependency line goes into a report, re-read the authorizing prompt for that exact task:

| If the prompt… | Then report… |
|---|---|
| already grants the action ("no extra approval gate between manager-verified proof and I1/I2") | the **correctness prerequisite** that still stands (e.g. "COMFY micro matrix + lightweight server proof + BENCH isolation must pass first") — never an approval gate |
| already authorized a step after a freeze you control (QA after INT freeze) | the freeze state as a *sequencing fact* ("candidate f991e243 frozen; QA may run") — not as permission you are waiting for |
| genuinely defers to Codex (C-CONTRACT, production integration) | that gate, named exactly, as `BLOCKED_DEPENDENCY` |

When a correction says the old wording "must not survive the final packet", fix the **delivered documents**
(REPORT/NEXT_REVIEW_PACKET/proposal), not just the chat message — the packet is what the next reviewer reads.

## 9. Autonomous 24/24 Heartbeat & Telegram Delivery

When the user asks for periodic updates to Telegram (e.g., every 30m) during continuous autonomous execution:

- **Always use `parse_mode="HTML"` for Telegram API.** Telegram Bot API's `parse_mode="Markdown"` (v1)
  fails with `HTTP Error 400: Bad Request` whenever messages contain unescaped underscores, brackets,
  or symbols common in software development (e.g. `r6_cache.py`, `_stage`, `TASK_C02B2`, `f_0001_key.png`).
  Use HTML tags (`<b>`, `<i>`, `<code>`, `&gt;`, `&lt;`) which cleanly tolerate code tokens and snake_case paths.
- **Direct Bot API delivery when gateway polling conflicts.** If `hermes gateway` is disabled,
  has a token conflict (`409: Conflict` on `getUpdates`), or cron delivery cannot reach desktop chat,
  deliver heartbeats directly via `https://api.telegram.org/bot<TOKEN>/sendMessage`.
- **True Liveness Audit in watcher daemon (anti-phantom heartbeat).** A watcher daemon
  that only reads `STATE.json` will produce a **phantom heartbeat (báo cáo láo / fake liveness)**
  if the agent goes idle. Because `STATE.json` says `status: RUNNING`, the daemon will blindly
  spam "Đang chạy 24/24" every 30 minutes for hours while zero worker processes are alive and
  zero tokens/progress are being generated. The daemon **MUST** inspect the file tree's latest `mtime`
  and actual worker PIDs on every tick. If no file has changed in >10 minutes, the heartbeat
  MUST loudly declare `⚠️ STALL / IDLE — Không có tiến trình hoạt động (Agent đang chờ lệnh)`
  instead of reporting a fake `RUNNING`.
- **Turn-based session vs Continuous background execution.** In an interactive desktop chat
  session, the LLM agent stops executing when its turn finishes. Never tell the user "hệ thống
  đang chạy tự động 24/24" unless an actual persistent worker loop or script is running in the
  OS background. If work is executed turn-by-turn by the agent, state plainly that execution
  happens per turn.

## Pitfalls

- **Phantom heartbeat / fake liveness loop.** A watcher daemon reading `STATE.json` blindly
  repeats `status: RUNNING` while the agent is sleeping between turns. The user receives regular
  "Đang chạy 24/24" pings but sees 0 router usage and 0 git/file changes. Always verify latest
  mtime (<10 min) and active OS PIDs before claiming a task is actively running.
- **Telegram Markdown parsing failure on code tokens.** Using `parse_mode="Markdown"` with filenames
  or variable names containing `_` silently throws `HTTP 400: Bad Request`. Use `parse_mode="HTML"`.
- **Half-translated report.** English section headings over Vietnamese prose still reads as
  ignoring the preference — translate headings too, keep only tokens verbatim.
- **Reporting a worker's exit code as the verdict — in either direction.** `exit 0` can mean "ran out
  of turns mid-work", and `exit 1` can mean only `hermes -z: no final response was produced` (a 72-byte
  log) while the lane had already committed its work, written its REPORT and its evidence set. Read the
  log payload (`wc -c` it: ~70–130 B of API/CLI error = infrastructure, several KB = a real report) and
  measure the disk (commit + `porcelain` + evidence count) before labelling a lane finished or failed;
  then resume only the true remainder. Never re-run a lane whose work is already on disk.
- **Reporting a replayed exit notice as new work.** See §6 — identify it against the ledger first,
  and never re-dispatch on a notice whose lane is already recorded as resumed.
- **Calling a worker's number unreproducible too early.** Before contradicting a reported digest,
  a wall time or a pass count, exhaust the obvious explanations (hashing/canonicalisation choices,
  wait vs wall vs server time, a template's normal multi-pass loop). Retracting your own wrong
  claim in the message that carries the corrected measurement costs one sentence; letting it stand
  devalues the whole verification.
- **Burying the slip.** A late ETA change mentioned four messages after the optimistic table
  reads as concealment.
- **Probing a mutating script with `--help`.** A script without `argparse` executes on
  invocation; read its source first (this cost one round of shutdown evidence).
- **Silence while work continues.** >20 minutes of silence during active work is treated as a
  problem; heartbeat with real numbers, audit at 8 minutes without progress.
