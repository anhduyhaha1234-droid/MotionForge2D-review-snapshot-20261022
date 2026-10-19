# Manager Evidence Verification, Manifest Scoping, and Freeze Protocol

Manager-side patterns for verifying worker claims, guarding write-sets, and
handing a frozen artifact to a read-only evaluator. Class-level; no
session-specific IDs below.

## 1. Verify a receipt, never accept it

A worker's exit code, its report, and even its own "gate PASS" line are
self-reports. Re-run the decisive commands yourself and compare against the
claimed numbers. The cheap set that catches most false greens:

| Claim | Manager check |
|---|---|
| "suite is green" | re-run the exact suite command in that worktree; compare pass/skip counts |
| "commit X on branch Y" | `git rev-parse HEAD` and `HEAD^`; parent must match the stated parent |
| "allowlist only / N files" | `git show --stat HEAD` — count the paths, confirm none outside the allowlist |
| "not pushed" | `git branch -r --contains HEAD` (empty = on no remote) |
| "clean tree" | `git status --porcelain | wc -l` |
| "only these files changed, all grew" | `sha256` + line/byte count each path against the pre-write manifest; a **shrink** is the signal |
| "test named exactly `<name>` exists and passes" | run `pytest -k <name>` — do not accept a suite count as proof a named row exists |
| "committed bytes == reported bytes" | `git show HEAD:<path> \| sha256sum` vs the hash the worker reported |
| "protected set untouched" | re-run the guard verify; expect `VERIFIED, 0 failures` |

Record each check's real output in the Manager report. If a worker's terminal
state is `RUNNING` rather than `SUBMITTED` while its evidence set is visibly
complete, that is usually the iteration cap, not a blocker — verify what is on
disk and open a narrow continuation for the remainder.

## 2. Hash snapshots, not filename lists, for untracked write-sets

Filename-only guards, and mtime-only checks, cannot distinguish "bytes changed"
from "bytes re-written identically". When a task's write-set is untracked (so
`git diff` proves nothing), snapshot bytes with hashes BEFORE the worker runs and
diff hashes after; report "mtime touched, content byte-identical" rather than
"files changed". Note that a tool cache (`__pycache__`, `.pytest_cache`) and a
test that re-invokes the project's own generator both produce benign mtime
churn — check `git check-ignore -v <path>` before calling something a stray file.

## 3. Manifest scoping — the protected set must EXCLUDE the active write-set

Symptom of getting this wrong: the guard verify reports N `protected_file_changed`
failures whose paths are **exactly the task's own write-set files**. That is not
worker damage; it is a Manager manifest error, and if left unrepaired it either
cries wolf on every re-verify or, worse, trains you to ignore the guard.

Rule: one protected manifest holds only files no active writer may touch. Each
task gets its OWN write-set manifest (preimage hashes + byte snapshots) checked
separately. When you discover the overlap:

1. subtract the task write-set from the protected manifest and write a corrected
   manifest alongside it (never overwrite the original — keep the mis-scoped one
   as history);
2. re-verify; expect 0 failures;
3. state the reclassification in the report, naming how many entries moved.

Do this BEFORE dispatching further writers: a mis-scoped baseline silently
under-protects the files you actually needed guarded.

## 4. Freeze before the evaluator reads — never evaluate a live root

Dispatching a read-only evaluator against a candidate while the artifact's owner
is still writing sibling evidence in the SAME root is a coordination defect even
though the candidate bytes may be untouched. Symptoms a good evaluator will
report back at you: "files under this root were modified during my run",
"another writer is active". Consequences: mixed reads of the JSONs around the
artifact, and a review that cannot be reproduced later.

Protocol:
1. writer reaches terminal (session `agent_close`, workspace clean);
2. **then** the Manager snapshots the whole input subtree — media, run records,
   graphs/workflows, frame/label maps, pins, measurement JSONs — into a NEW
   freeze id, with a hash manifest (per-file sha256, bytes, mtime) and a
   `hash_mismatch == 0` check;
3. the evaluator reads ONLY the frozen copy;
4. a correction means a **new candidate id and a new freeze** — never reuse an
   existing freeze path and mutate the files a review already read. A report is
   never re-pointed at a mutated path.

Keep the freeze tool deterministic (copy + re-hash + manifest) and refuse to
write into a non-empty freeze id, so a re-run cannot silently blend two
candidates.

## 5. When a report's narrative contradicts its own artifact, the ARTIFACT wins

Real case shape: the artifact records `UNPROVEN` plus a collateral-damage
incident, while the worker's prose says `CONFIRMED`, explaining the extra pid
away. Both cannot stand in one evidence set.

Resolution, in order:
1. re-derive the physical end state yourself (is the port actually closed, is
   VRAM back to idle, are the Manager's own processes alive?) — that tells you
   whether the underlying outcome was in fact achieved;
2. classify the disputed item from evidence, not from the prose. A client
   connection row (`ESTABLISHED <pid> -> <port>`) plus the process's own cmdline
   in a before-dump is enough to prove "our own client process", which changes
   the verdict wording rather than the measurements;
3. rewrite the artifact so its verdict line matches the evidence; **keep the
   superseded verdict verbatim in a block inside the same file** — never delete
   it;
4. require a read-only re-check that changes no measurement and starts no
   engine, and that records which fields changed (a `report_only` field set);
5. ask for adversarial cases proving the classifier cannot emit the strong
   verdict on thin evidence (missing chain, missing dumps, timeout code instead
   of a closed port, empty set must NOT count as success).

An empty set proving "success" is the classic false-green here: absence of
evidence is not evidence of absence.

## 6. Scope continuations narrowly — expect 2–3 rounds per task

The worker CLI stops at its iteration budget mid-way through a multi-artifact
task, usually right before the documentation/evidence-set step, and self-reports
`RUNNING` honestly. Plan for this instead of treating it as a failure:

- order the packet so the **decisive artifact** (the clip, the passing test, the
  real-server proof) is produced in the FIRST half of the budget;
- keep documents/evidence-set/commit in the same packet but late, so a
  truncated round still leaves the hard part done;
- a follow-up round should be cheap and narrow: write the N documents from
  numbers already on disk (say explicitly "do not re-measure"), close the one
  remaining boundary item, commit;
- if a packet grants no git authority, the worker will (correctly) leave the fix
  uncommitted — then a reviewer cannot tell which bytes they reviewed. Open a
  separate **commit-seal** round whose entire scope is: verify HEAD/porcelain
  match the reported set, add the explicit paths only (never `git add -A`),
  commit, prove parent intact + tree clean + not on any remote.

## 7. Gates run in one order, and a green on one row never waives another

micro (named tests) → finite matrix with 100% of rows dispositioned (no silent
skips) → focused/static (lint on the touched files only) → the expensive proof
(real server / GPU run) → evaluation on the frozen artifact. A broad suite being
green does not discharge a specific failing row; keep the failing row visible in
the matrix with its measured values.

## 8. Protect the evidence a service-lifecycle step can overwrite

Shutdown/service-control steps are the most common place a run silently eats its
own evidence. Three rules to put IN the packet:

- **Capture before acting.** Snapshot the before-state (listeners, pid sets,
  VRAM, port probe) to files first; only then stop anything. A capture that runs
  after the stop records nothing useful.
- **A script without `argparse` RUNS when called with `--help`.** Trying to "read
  the options" invoked a stop tool, which performed the shutdown and overwrote
  the previous round's evidence record — unrecoverable. Tell workers explicitly:
  read the source of any tool you did not write before invoking it, and treat
  `--help` / `-h` / `--dry-run` as *unverified* flags, never safe probes. Never
  probe a possibly-destructive tool by running it.
- **Distinguish "own client exited" from "we killed it".** A pid-set diff that
  removes an unexpected process is not automatically collateral damage: check
  the before-dump for that pid's cmdline and for a connection row tying it to the
  service (`ESTABLISHED <pid> -> <port>`). Own client that exited by itself ⇒
  reword the verdict, keep `collateral_removed` empty and record the
  classification separately; cannot prove ownership ⇒ leave the verdict
  unproven. Never upgrade a verdict on an assumption.

## 9. Keep the failing/negative evidence, verbatim

Every round's superseded verdicts, mis-scoped manifests, broken first attempts
and destroyed files stay in the tree as named history ("superseded", "incident",
"first-pass"). A correction record that deletes what it corrected cannot be
audited, and the next reviewer will re-derive it. State the loss plainly when
bytes are unrecoverable — an honest "not recoverable, not reconstructed" beats a
plausible rebuild, and a rebuild presented as the original is the worst outcome.

## 10. Report in the user's language, with numbers first

When the user works in Vietnamese, the Manager's whole status reply is in
Vietnamese — headings, prose, verdicts, explanations, and the "what is still
open" list. Keep technical tokens as-is (paths, shas, commit ids, error codes,
`TASK_SUBMITTED`, tool names); do not translate those, and do not let them
justify drifting the surrounding sentences into English. A reply that is half
English because the tables and verdicts were drafted in English will be
corrected — draft the framing in the user's language from the start.

Report shape the user expects on every status turn:

1. lead with status, not with a plan;
2. real measured numbers (counts, sha256, ports, timings, VRAM) — never "looks
   good" or a restated claim from a worker;
3. an ETA table date-anchored to the local date, with what is parallel vs
   serial-forced and the single riskiest lane;
4. the gaps/limits listed explicitly — the user reads the "still open" section
   as the most important part and treats a report that hides one as a defect;
5. the final review packet returned in chat for the user to forward; the Manager
   never sends review/APPROVED/CLOSED itself, and never opens the next stage
   without direction.

When a deadline slips, say so in the same turn it slips, with the reason — the
user has stated that a silently-slipped ETA is not acceptable.
