# Long-scope RUN bootstrap — hash-gated inputs, absolute deadline, new-Manager takeover

Continuation of `authority-doc-edits-and-proposed-only-loads.md` (MotionForge2D
MF-DEMO-LONG-01, 2026-10-05). Previous turn ended at RULES_LOADED + PREFLIGHT_OK
with NO RUN and NO dispatch. This turn the user said **"làm đi"** — that is the
explicit execute-the-packet command. The work then is *Manager bootstrap only*:
build the RUN, pin the budget, mint the worker. None of it touches
production/test/UI/config.

## 1. "làm đi" / "cứ làm đi" after a PROPOSED_ONLY load = authorization to execute

Do not re-ask. But also do not over-read it: it authorizes the packet's declared
scope (RUN tree, registry, budget, one worker dispatch) — not scope the packet
excluded (here: no code/UI/integration, those stay `BLOCKED_DEPENDENCY`). The
"stop and report" from the load turn is now superseded by one clear go signal.

## 2. One deterministic bootstrap script, not a pile of ad-hoc commands

Build RUN + D + `manager/{tools,packets,registry,evidence}` and the D subtrees
(`source/style/graph/scripts/cache/env/evidence/output/temp/user`) with one
`write_file`'d Python script invoked as `cd <dir> && python -B ./setup_run.py`.
Benefits seen: idempotent dir creation, one pass of the gates below, one receipt.
Make the RUN name deterministic with an **env var** (`RUN_TAG=$UTC-wan-long`),
defaulting to a timestamp if unset — re-running the script reproduces the same
tree instead of minting a second RUN.

## 3. Hash-gate EVERY locked input before use — copy-verify, fail closed

For each input the packet pins (source video, style PNG, reuse graph, the packet
itself, the rules file), the script did:

```
got = sha256(src)                       # hash the SOURCE first
assert got == packet_sha and size == packet_bytes   # fail-closed before any copy
shutil.copy2(src, dst)
assert sha256(dst) == packet_sha        # re-hash the COPY
# any mismatch -> INPUT_GATE_FAILED, abort the whole bootstrap
```

Never let "the file exists" stand in for "the bytes match the hash the packet
pinned". Snapshotting the locked inputs into `D/` at bootstrap means the worker
never reaches across to a path another job could mutate.

## 4. Pin the absolute deadline ONCE; store the epoch, not a per-round timeout

The prototype harness bug (named in the packet §3, and visible in
`dispatch_w2.py:28,130`) was `DEADLINE_SECONDS = 21600` re-applied on **every**
resume — six hours fresh each round, which is not a deadline at all. The correct
shape, written into `BUDGET.json` at first dispatch:

```
"first_dispatch_utc": <now>,
"absolute_deadline_utc": <now + 48h>,
"absolute_deadline_epoch": <epoch float>,
```

Every later continuation computes **remaining = deadline_epoch − now** and refuses
when `<= 0`. Keep a boolean note that 48h is a HARD STOP, **not an ETA** and not a
target to consume. Do the same for the counting caps (chunk N, correction K,
video/image/vision caps, worker/manager attempt caps) — all in the one BUDGET.json,
with a `counts_so_far` block where every unmeasured counter is the **string**
`"UNKNOWN"` (never `0`, which reads as a measured zero).

## 5. Reconcile the prior prototype's cost into a sibling receipt

The new scope must not hide old spend. Read the previous run's append-only
`DISPATCH_LEDGER.jsonl`, count dispatches/terminals, extract the worker-terminal
rows (cause + candidate slots used), and write
`manager/registry/PROTOTYPE_COST_RECONCILED.json` recording: deadline status
(`EXPIRED …; NOT revived`), preserved owner id, cause (`output-length truncation
on a monolithic response; not quota`), and `worker_model_attempts: "UNKNOWN"`.
Prototype here used 0 candidate/video/image slots — say so explicitly rather than
leaving the count ambiguous.

## 6. Registry + append-only ledgers

`SESSION_REGISTRY.json` holds three blocks: **manager** (this takeover),
**worker** (`session_id: null` + `status: PENDING_DISPATCH` until the dispatch
happens — record ID/model/write-set BEFORE the first write), and **preserved**
(the old prototype owner, read-only lineage). Plus the `blocked_dependency` list.
Open `DISPATCH_LEDGER.jsonl` and `BUDGET_LEDGER.jsonl` with mode `"a"` and stamp
one header row per run — never `"w"` (a `"w"` reopen destroys prior history; see
the ledger-truncation pitfall in terminal-engineering-discipline #29).

## 7. New Manager on explicit go = takeover, not a blind resume of a stale one

The packet said "use manager `20260930_235002_3ac7f9` if still recoverable; if the
user hands a new Manager, record a takeover with zero duplicate controller." That
old session's last message was ~4 days earlier with 505 messages. Correct handling:
take over in a **new** session and record in the registry
`previous_manager_context_health: STALE ~100h / 505 msgs -> NOT resumed`, the
previous id + last-activity timestamp, and `zero concurrent controller`. Do **not**
resume blind, and do **not** transfer a *worker* owner just because its history is
long — the same rule (rules §4) distinguishes "stale manager, new Manager takes
over" from "long-lived worker, keep the same owner".

## 8. Preflight values to emit (measured only)

`nvidia-smi --query-gpu=… --format=csv,noheader,nounits` (index/name/total/used/
free/util), `netstat -ano | findstr LISTENING` filtered to the ports of interest,
the custom router port (here `127.0.0.1:20128`), `df -h /c` for disk, and a RAM
figure. On this Windows/git-bash host the `GlobalMemoryStatusEx` ctypes struct
returned all zeros; `wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /value`
is the working hook. Report the RAM as free/total KB → GiB, and label every number
as a snapshot (it does not prove the memory stays free).
