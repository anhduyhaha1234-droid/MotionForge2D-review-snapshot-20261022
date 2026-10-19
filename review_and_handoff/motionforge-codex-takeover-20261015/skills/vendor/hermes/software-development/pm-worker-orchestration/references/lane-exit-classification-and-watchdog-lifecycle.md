# Lane exit classification & watchdog lifecycle

Measured 2026-09-24 across a six-lane correction round (COMFY, P1QC, CONTRACT, VIDEO14B, BENCH,
S12-QA) in which **every lane returned `exit 0`** — and only some of them had finished. The exit
code carried zero information; the launcher log payload carried all of it.

## 1. Classify every lane exit from the LOG PAYLOAD, not the exit code

| Log payload | Meaning | Correct response |
|---|---|---|
| **~124–125 bytes**, single line `API call failed after 3 retries: HTTP 503: […] [502]: fetch connect timeout (reset after Ns)` | upstream flap — the worker may have done nothing, or been cut mid-turn | §9 cycle: byte-safety first, wait ≥5 min, resume same owner/model/scope; state `RUNNING_RETRY_WAIT` |
| long log (>5 KB) ending in the worker's own report | the run reached its end — read the report's terminal line | verify, or send a finish packet (§2) |
| long log whose tail is the API-error line (after a complete report/commit on disk) | the worker finished its work and died at the **final chat turn** | confirm-don't-redo resume (§2) |
| 0-byte log with a live process pair | normal while waiting on the model | leave it alone |

Measured spread in one round: COMFY/P1QC/CONTRACT each ended `exit 0` after 48–63 min of real work;
P1QC and CONTRACT ended with a self-declared `RUNNING` + a 3–4 item gap table (out of turns);
BENCH and S12-QA later died on flaps with 124/125-byte logs. Reading `log_bytes` first tells you
which of the three you are looking at before you spend a verification cycle.

## 2. Two different resume packets — never one text for both causes

* **Out of turns** (log ends with the worker's own gap list): send a **finish packet**. Say plainly
  "your run ran out of turns, not into an error"; **quote the worker's OWN remaining-steps list
  verbatim** (it usually names the exact commands — reuse them, don't reinvent); forbid redesign;
  give a small budget (~35–60 tool calls). The lane then writes the missing REPORT, re-anchors the
  one stale measurement, commits, and reports.
* **Flap** (log ≈125 B): send a **confirm-don't-redo packet**. Lead with the byte-safety result and
  enumerate what is already measured-DONE on disk (commit SHA, report bytes, evidence filenames),
  then "do not re-run the round". For a lane that had already written its report + commit, the
  resume is a ~20-minute confirmation, not a second working session.
* Both keep: same owner session, same model, same scope, fallback OFF, and **one packet file per
  lane per round** (that is what keeps the requested→actual id mapping provable).

## 3. Byte-safety FIRST — a mid-flight death is not automatically a loss

Before choosing the packet type, measure: `git status --porcelain` per tree, evidence-dir
mtimes/sizes, and the post-worker guard. Measured outcomes from the same round:

* one lane died with **3 in-allowlist paths uncommitted + preimage JSONs written minutes earlier**
  → the resume must say "re-read your own leftovers first, state what is done vs open";
* one lane died having written **nothing new** (nothing in its evidence root post-dated the
  resume) → plain retry of the same packet;
* one lane had **already committed**, and only the final chat turn was lost → confirmation run.

A `RUNNING` self-report from a dead worker is honest state, not a failure — and it is also not
`TASK_SUBMITTED`. Keep the distinction in the registry.

## 4. Watchdog lifecycle — re-point it whenever the lane set changes

A watchdog keyed on session-row growth must be taught the difference between "no progress" and
"finished":

1. **Receipt-aware DONE.** The launcher writes a receipt when the run returns. A lane whose receipt
   exists is FINISHED — exclude it from stall detection, or every clean exit re-reads as an
   eight-minute stall ~9 minutes later. Measured: a false `STALL DETECTED` on a lane whose run had
   ended 9 minutes earlier; the §7 audit (receipt + log tail) resolved it as *exit*, not hang.
   Diagnose, then teach the watchdog — never suppress the stall check globally.
2. **Stale PID lists cause "all exited" false alarms.** A watchdog still holding the previous
   wave's PIDs fires `ALL WAVE-A WORKERS EXITED` while three NEW runs are alive. The same applies
   to session ids after `--resume` mints a new one: re-derive, then re-point BOTH the ids and the
   PID list before restarting the watchdog.
3. Restart the watchdog at every lane-set change, and log which wave a sample line belongs to.
4. A watchdog exiting on its own finite window means "window over", not "task complete".

## 5. Capacity: two flaps inside 60 s is a signal to reduce, not to push

Policy stays: **never** switch model/provider to dodge the error; keep cycling same-owner resumes
with the ≥5-minute floor and the 45 s stagger. But when consecutive flaps appear at the cap, drop
to 2 concurrent streams and record the reason in the heartbeat — the concurrency cap is a measured
resource limit, so lowering it is a finding, not a preference. Also note the flap is
provider-wide: resume each dead lane with its OWN continuation packet (§2), never one merged text.

## 6. Shell-level trap when sweeping lane trees: colon-delimited parsing

Looping over `"C:/Users/.../wt-comfy:COMFY"` and taking `${t%%:*}` yields **`C`** — a Windows drive
letter is itself a colon. The next command then reports `fatal: cannot change to 'C'`, which reads
like a missing directory rather than a parsing bug, and the loop printed `0` changed paths for
*every* lane (a blanket near-impossible result is a bug signal, not a finding — see
`references/continuation-monitoring-and-vacuous-guards.md` §2 for the same class of near-green).
Use a delimiter that cannot occur in the data (`|`), or split inside a Python one-liner. On this
host, shell-level string handling of paths is a recurring source of false failures.
