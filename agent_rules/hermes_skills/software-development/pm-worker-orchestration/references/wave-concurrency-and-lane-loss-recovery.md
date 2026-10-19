# Wave concurrency, lane-loss recovery, and session↔lane provability

Measured across a 24-dispatch / 25-receipt CPU+GPU wave (7 lanes, ~7.5 h wall). Every rule below
came from a failure that actually happened on the box, with the numbers that exposed it.

## 1. Cap concurrent worker streams at 3, stagger starts ~45 s

**What happened:** dispatching 7 lanes simultaneously correlated with **two upstream 502 flaps inside
50 minutes** — the first killed 6 of 7 lanes, the second killed all 7. Reducing to **3 concurrent
streams with a 45 s stagger** ran clean for the rest of the wave with no further flaps.

**The failure signature:** the launcher printed `exit 0`, and its log was **exactly 125 bytes**:

```
API call failed after 3 retries: HTTP 503: [<provider>/<model>] [502]: fetch connect timeout (reset after 11-29s)
```

**Rules:**
- The provider caps *concurrent* streams, not just request rate — serialising starts and holding ≤3 open
  is the mitigation that worked. Raise concurrency only with evidence, not optimism.
- Never treat the flap as a task result. Classify it `RUNNING_RETRY_WAIT`, **wait the full 5 minutes**,
  probe the route, then resume the **same** owner/model/scope. No blind retry, no owner swap, no fallback.
- Budget ~40 min of wall clock for a two-flap wave when estimating the next packet.

## 2. `exit 0` from a CLI launcher is not evidence of work

Three separate times in one wave the launcher returned `exit 0` while the log held nothing but a 502
payload, and six of seven lanes "exited normally" having done nothing. A third shape below produced
`exit 0` with **no log at all**.

**Gate on the log payload and the on-disk artifact, never on the exit code.** A cheap content check:
log size + presence of the expected report marker. Keep the payload as the evidence of *why*.

## 3. Three distinct lane-loss shapes — check the process table, not the receipt

| Shape | Log | Session row | Signals |
|---|---|---|---|
| Upstream 502 flap | 125 B error payload | `ended_at=null`, no `agent_close` | log payload |
| Silent kill | **no log at all** | `ended_at=null`, no `agent_close` | **only** the no-progress rule |
| Budget exhaustion | real report, status `RUNNING` | `ended_at` set | report states the gap |

The silent kill is the dangerous one because the background-completion notice **never arrives** (the
process was killed, not exited) — so the receipt cannot be trusted to tell you anything.

**§-rule that caught it (keep it):** *no fresh progress for 8 minutes ⇒ inspect immediately.* Tie it to
three independent reads, because any one alone lies:

1. session counters (`message_count`, `tool_call_count`) frozen across successive polls;
2. **newest evidence-file mtime** under the lane's evidence root (use `os.path.getmtime`, not
   `find -newermt` — the latter is timezone-shifted under git-bash and returns false alarms);
3. the live process table — the worker is simply **absent**.

`ended_at = null` is **not** proof of liveness, and the *absence* of a completion notice is **not**
proof of work.

## 4. Recover by resuming, never by re-running

Before re-dispatch, **snapshot the WIP** (per-file sha256 + dirty/manifest listing). Then send a resume
packet that says, explicitly:

- "your previous attempt ended unexpectedly; **that is not a task result**";
- "your work is intact — here is the list of artifacts found on disk, with sizes";
- "**do NOT re-run** the measurement / re-render / re-decode / touch the GPU";
- "the whole remaining gap is: write `<report>.md` from the JSON you already produced, restate the
  sentinel with numbers, make the local scoped commit."

In one case the crashed lane had already written 8 evidence files **and** a full 49 KB result JSON
before dying; re-running would have burned the window for zero new information. The resume round then
completed in ~8 minutes against a ~20-minute original.

## 5. Session↔lane provability: one packet file per lane per round

**What happened:** three lanes were resumed with ONE merged packet ("read the section matching your Task
ID"). Afterwards the mapping was **unprovable**: all three sessions' first user message is byte-identical
(the whole packet), and this Hermes `state.db` records **no resume parent** — `parent_session_id`, `cwd`
and `title` are all NULL for worker rows. A UI-only echo like `[terminal] ran \`…\`` is **not stored**,
and tool *results* echo the packet text, contaminating any keyword count.

**Rules:**
- **One packet file per task per round, even when 95 % identical.** That single fact is what makes
  `first-user-message == packet head` a valid proof.
- Derive the mapping from ground truth: read each session's **first user message** from the read-only DB
  and match it against the packet text. **Never** infer it from dispatch order or timestamps — doing so
  produced **4 wrong of 6** pairs (two swapped), and three wrong pairs in a later round.
- `--resume` mints a **continuation id that does not track dispatch order**, and several sessions can
  share the same start second.
- **Grade every row** in the ledger: `PROVEN` (content match) / `CONFIRMED` (worker reads its own
  `HERMES_SESSION_ID` and it matches) / `INFERRED` (order + stagger only, because a merged packet made
  proof impossible). Never present `INFERRED` as proven; write the proof method into the row
  (`actual_session_proven_by`) so a reviewer can re-derive it.
- Two lines of evidence can upgrade a row: when the worker self-reports its env id and it matches the
  inferred value, promote `INFERRED → CONFIRMED`.

**Ledger hygiene:** a hand-backfilled append-only ledger accumulated duplicates and one row pointing at a
receipt filename that never existed. Do not rewrite raw history — emit a reconciled file plus a
reconciliation note, and assert `receipt files on disk == dispatches` as a cheap structural check.

## 6. A file written just before a crash is UNEXECUTED code — run it

Two lanes' prior rounds died before execution, leaving ~3.5k lines of code that had **never once run**.
Executing it surfaced **nine** real defects invisible to reading:

- an argument order swap (`is_within(path, root)` called reversed) that made every artifact fail with the
  *wrong* error reason — 16 tests failing for a bogus cause;
- an import from the wrong module inside a bare `try/except Exception`, so a silent fallback won and read
  the wrong root — a `422` on real evidence;
- a `state == 'ready'` filter that **silently** fell back to an older render (green-by-fallback);
- a crop taken *inside* the expected bbox while the signal lies *outside* — the measure was structurally
  `0.0` by construction;
- a `@property` returning a hardcoded `False` (fake logic), and a flag turned into a constant.

**Rule:** `py_compile` + linter + "the file exists" are **not** evidence. Run the artifact, and for a
constant-valued property replace it with a real deterministic answer or delete it. "A resume packet's
'you wrote nothing / tree is pristine' claim is hearsay" — measure `git status --porcelain` and compare
file mtimes against the checkout time to date a stray artifact.

## 7. Gate self-checks worth automating in the final gate script

A 70-check gate caught real defects in the Manager's own deliverables. Include:

- every required document **exists and is non-trivial in size**;
- **no self-approval token** anywhere (`QUALITY_ACCEPTED = 1`, `STATUS: APPROVED`, `APPROVED_BY_MANAGER`)
  and the terminal state string present where the state is claimed;
- **markdown table integrity**: `"\n||"` absent (a fuzzy `patch` on a table silently deleted a row and
  doubled the leading pipe, and every row edit reported success), plus an explicit "all expected row keys
  present" assertion — patching a table and inserting a paragraph mid-table both corrupted it this run;
- **frozen-artifact hash re-verification** from the manifest (compare `.lower()`; verify you are hashing
  the same copy the manifest hashed — a 194/194 "all corrupted" result was two comparison bugs);
- **receipt count == dispatch count**;
- ports refuse connections and GPU is idle (engine really shut down);
- commits local with **intact parents** and `git branch -r --contains HEAD` empty;
- session↔lane mapping grades present in the registry.

## 8. Freeze after the writer is terminal — then the evaluator reads only the frozen copy

Sequencing that held: writer terminal → capture freeze (new id, never edit inside an old freeze) →
dispatch the evaluator against **the frozen copy only** → new candidate ⇒ **new freeze id**. Any
corrected candidate leaves every reviewed path untouched.

## 9. Spell literal evidence paths in every packet

Defining an alias once (`**NEW:** <run-root>`) and then instructing "put evidence under `NEW/<TASK>/**`"
was read **two ways**: two of seven lanes created a **nested** `NEW/NEW/<TASK>/…`. Both spellings held
real hashed artifacts. Write the literal destination (`<RUN_ROOT>/<TASK>/raw/x.json`) or a worked example.
Once bytes are hashed, **never move them to tidy up** — record the real path in the manifest/registry and
treat the path as data, because a silent move destroys the reviewer's ability to recompute the hash.

## 10. Report the split verdict honestly

When one row has sub-claims, disposition them separately rather than collapsing to a single word —
e.g. `G: PASS · I: PARTIAL · V: NOT_REVIEWED`, with an explicit statement that a green suite cannot close
the visual half. Also flag harness **vocabulary artefacts**: a runner printing `TECHNICAL=TECHNICAL_FAIL`
because `UNMEASURED ∉ {PASS, NOT_APPLICABLE}` had **0 FAIL rows** — say so in the report and the matrix,
or a reviewer will read it as a failed check. Keep `accepted seconds = 0` explicit so cost-per-accepted
-second stays **undefined** instead of being silently computed from wall time.
