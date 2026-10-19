# Packet path drift + relaunch semantics (measured 2026-09-27/28, MotionForge delivery)

These are evidence-integrity lessons from a Manager round where dispatch packets
sent two workers into a WRONG evidence root. Read this before dispatching workers
whose deliverables land in a shared evidence tree.

## 1. Evidence-root path drift — two sibling dirs, one hyphen apart

**What happened.** The canonical R28 evidence root was
`C:/Users/Admin/Documents/Codex/2026-09-27/c-v-th-c-hi-n/outputs/r28-cpu-execution-20260927/`
(93 files). The Manager's new Phase-A packets retyped the path as
`…/c-v-th-c-h-i-n/…` — one extra hyphen. That spelling did not exist at write
time, so both dispatched workers CREATED it and wrote their first 6 artifacts
into the parallel tree (visible only as: canonical root unchanged, decoy root
with fresh mtimes 2 minutes old).

**Why it reads as data loss at first.** A later `find`/`ls` on the typo'd path
returns "No such file" while the canonical root holds everything — or the reverse
depending on which string you typed. Symptom: "the evidence root vanished / shrank
from 93 files to 6". Before believing a deletion: enumerate BOTH sibling names
with Python `os.listdir` on the parent and compare entry counts + mtimes.

**Containment playbook (worked, zero collateral):**
1. Stop writers by exact PID, leaf → root (agent python → hermes.exe → launcher
   python). Never `killall`/`pkill`/`taskkill /T`; after the kills, re-check each
   PID plus the bash wrappers and confirm the interpreter you must never kill
   (python.exe) shows no collateral change.
2. Byte-snapshot the orphan files into `RUN/manager/snapshots/incident_wrong_root/**`
   (with an INCIDENT.json recording why). Verify snapshot sha == source sha.
3. LEAVE the orphan files in place — never move/delete bytes that may be cited later.
4. Patch the packet: fix the path to the canonical spelling AND add an INCIDENT
   NOTE instructing the owner to COPY its orphaned artifacts into the canonical
   root under `raw/incident_wrong_root/` (plus a one-line README). Owners copying
   their own files is allowed; Manager moving them is not.
5. Relaunch the same sessions (stagger 45 s), then VERIFY the canonical root grows
   within the first minutes (list files newer than the relaunch time).
6. Append an incident row + relaunch rows to the append-only ledger.

**Prevention rule.** A human-typed path in a packet is data: copy it verbatim from
the authority document (grep the source doc for the exact string), never retype it
from memory. After every dispatch, list the canonical evidence root and confirm new
files appear — the decoy root's mtime is the tell.

## 2. `--resume` semantics differ by launch shape (state it in the registry)

* `hermes chat -q <packet> --provider … -m … --pass-session-id --resume <id>`
  → continues the SAME session row in place (measured: 196 → 247 messages,
  api 90 → 114, `end_reason` null again). `actual_session == parent`; grade the
  mapping PROVEN with the message-count delta as the proof.
* `hermes -z <packet> --pass-session-id --resume <id>`
  → mints a NEW successor id; resolve parent→actual by first-user-message == packet
  head (one packet per lane per round).

Do not wait for a successor that will never appear, and do not infer which shape
was used — check the DB row before writing the mapping row.

## 3. Silence ≠ stall: check the gate's known wall time

A lane with no new messages for ~300 s was running `pytest tests/product_p1`
(measured ~290 s on this host); the same pattern repeats with ~211 s matrices.
Before escalating on the 8-minute no-progress rule, compare the silent interval
against the durations of gates that lane is known to run. Probe process/GPU/logs
only after that comparison fails.

## 4. Launch receipt fields worth keeping

Record per launch: argv shape with model/provider pins, packet sha256 + bytes,
cwd, utc_start/utc_end, exit_code, duration_seconds, log path. Workers on this
host burn ~90 api calls per launch (turn budget); `exit 0` + a log whose tail says
the budget ran out is a "finish the last steps" resume, not a result.
