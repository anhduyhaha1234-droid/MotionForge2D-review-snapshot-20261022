# Multi-lane worker waves — dispatch, forensics and recovery

Measured 2026-09-23 on a seven-lane manager wave (3 correction lanes + 4 new tasks) that was killed
twice by the same upstream transport problem. Everything below is from that run, with the numbers
that made each rule non-optional.

## 0. The failure profile

Two bursts, ~50 minutes apart, each killed **every open lane at once**:

```
API call failed after 3 retries: HTTP 503: [<provider>/<model>] [502]: fetch connect timeout (reset after 5–29s)
```

Both times the launcher returned **`exit 0`** and the log was a **125-byte stub** containing only that
line. Six of seven lanes had produced nothing; one had produced real work. The route answered
`HTTP 200` + a successful chat probe again after each burst, so this was **transient transport**, not
auth/quota/config — and therefore not a typed blocker.

## 1. Identity: the shared packet destroys provability

A merged resume packet ("read the section matching your Task ID") was used for three lanes at once.
Consequences, all verified against the read-only session DB:

- Every lane's first user message is **byte-identical**, so `packet_head in first_message` cannot
  discriminate them. It matched all three, and "newest wins" picked the wrong ones.
- That DB records **no resume parent** for worker rows (`parent_session_id`, `cwd`, `title` all NULL),
  so lineage cannot resolve them either.
- Tool **results** echo the packet text, so any keyword count over result bodies is contaminated —
  a count over results gave `{COMFY: 9, BENCH: 8, VIDEO: 8}` for one lane, i.e. noise.
- The `[terminal] ran \`<cmd>\`` prefix is a **UI rendering**, not a stored column — grepping for it in
  the DB returns zero matches, so it cannot be used as the discriminator.
- The launcher did not record the minted session id anywhere early (it writes the receipt only after
  the child exits), so there was no dispatch-side record to fall back on.

Result: the mapping had to be written as **`INFERRED`** (dispatch order + the 45 s stagger, whose
session start times matched the launch order exactly). That is the honest grade — but it is a worse
outcome than proving it.

**Rules learned**

1. One packet file per task per round, even at 95 % content overlap. It costs one extra file and makes
   identity provable.
2. Confirm by asking the worker to read **`HERMES_SESSION_ID`** from its own process env and report it.
   In this run one lane did exactly that and its self-reported id matched the inferred one, promoting
   the row from `INFERRED` to `CONFIRMED`. Cheap, and it settles the question.
3. Grade every row in the ledger, e.g.

   ```json
   {"task": "...", "round": "c2b",
    "parent_session": "...", "actual_session": "...",
    "actual_session_proven_by": "INFERRED: dispatch order + 45 s stagger (shared packet prevents content proof); pending worker self-report"}
   ```

4. Never reason "oldest batch first, then creation order". That heuristic got **4 of 6** rows wrong in
   the first attempt of this run, silently swapping two pairs of lanes.

## 2. Damage assessment before re-dispatch

After a shared outage, lanes split **unevenly**. Measured footprint per lane:

| lane | tree porcelain | tree HEAD | evidence files | WIP that mattered |
|---|---|---|---|---|
| A | 3 modified | unchanged | 51 | 3 patched source/test files |
| B | 4 modified | unchanged | 110 (102 under `work/`) | 4 patched files + a full reproduction rig |
| C | 1 untracked | unchanged | 0 | one new schema file |
| D | 0 | unchanged | 1 | one evidence file |
| E–G | 0 | unchanged | 0 | nothing |

So a blanket resume packet would have been wrong in both directions:

- "resume from scratch" throws away lane B's finished reproduction rig and 110 evidence files;
- "you already started, finish it" tells E–G to resume work that does not exist.

**Procedure before any re-dispatch**

```bash
for t in <tree1> <tree2> ...; do
  printf '%-22s p=%s head=%s\n' "$(basename "$t")" \
    "$(git -C "$t" status --porcelain | wc -l)" \
    "$(git -C "$t" rev-parse --short HEAD)"
done
# plus: evidence-root file count per lane, and log/receipt size per lane
```

Then snapshot each write-set (dedicated capture tool) so surviving WIP is diffable against a
known-clean baseline, and write the resume packet with **one section per Task ID** stating exactly
what is on disk and where to continue.

Watch for lanes that already **committed** before dying — check `HEAD` against the expected
pre-dispatch value; a changed HEAD with clean porcelain means the round finished and only the receipt
was lost.

The third shape is a lane that did **all** its work but died before writing its report and commit:
HEAD unchanged, write-set dirty, evidence root full. Its remaining gap is then only the prose + the
commit — and the resume packet must forbid re-running the measurement (see §4c).

Also budget for housekeeping the dead lane left behind: scratch files (`_tmp_*.py`) in the tree must
be named in the next packet so they are cleaned or moved before the next commit, and uncommitted
helper scripts from a budget-exhausted round must be either finished or explicitly declared open.

## 3. Concurrency as the lever

Two bursts ~50 minutes apart with seven long streams open. Response that worked:

1. classify (transient) rather than treat as a task result;
2. wait the stated interval and **re-probe the route, recording the probe** (`/models` 200 + a chat
   round-trip returning the expected token);
3. resume the **same** owner/model/scope — no new owner, no fallback model;
4. **reduce from 7 concurrent streams to 3**, choosing the lanes on the critical path first;
5. **stagger starts by 45 s** so the streams are not mid-request simultaneously.

The wave then ran clean for the remainder of the session. Keep the remaining lanes queued and dispatch
one as soon as a running lane's slot frees — that preserves throughput without re-inflating
concurrency.

## 4. Log payload beats exit code (three separate confirmations)

Over one session, `exit 0` coincided with "did nothing" three times:

| symptom | meaning |
|---|---|
| log == 125 bytes, body = transport error | round never ran; transient failure |
| log == 0 bytes, session row OPEN, tool count rising | lane healthy and still working |
| log several KB, session `ended_at` set, in-tree commit | round finished; read the report |

Practical gate: treat "log smaller than ~200 bytes" as a failure signal regardless of exit status, and
never mark a task submitted on the strength of an exit code.

## 4b. The silent kill — no log, no receipt, no notice

A **third** failure shape appeared in the same wave, distinct from both transport bursts: a lane's
process was killed at the process layer. Every signal was absent rather than wrong:

- the `.log` was **absent/empty** — not even a 125-byte transport stub to read;
- **no receipt** existed (the launcher writes it only after the child exits);
- the background-process **completion notice never arrived**, because the process did not exit;
- the session row had `ended_at = null` **and no `agent_close`** — on this host that combination means
  killed, not a clean end;
- the worker was **gone from the process table**, leaving only the two long-lived host processes;
- session counters (`message_count` / `tool_call_count`) stayed **frozen** for ~15 minutes while the
  newest evidence-file mtime aged past 8 minutes.

**Do not wait for a notice.** Run a stall check as soon as the evidence cadence slips:

```
1. session counters unchanged since the last heartbeat?
2. newest evidence-file mtime older than ~8 min?
3. worker pid absent from the process table?
   (match on the launcher/worker command line, not merely "python.exe")
=> any two of the three = inspect now; never assume "still working"
```

`ended_at = null` is **not** proof of liveness, and the **absence of a completion notice is not proof
of work** — the same rule as §4, extended to the case where there is no payload to read at all.
`agent_close` is the marker to grep for. Use the counter deltas as the *liveness* signal and the
evidence-file mtime as the *progress* signal; they answer different questions, and a lane can be alive
with no progress or dead with its work complete.

## 4c. A measurement lane that finished, then died

The killed lane above had already produced **everything scientific**: the full row verdict map, the
preflight, the sentinel ledger, the negative controls, the review manifest, pytest/ruff output and six
review artifacts. Only the **prose report and the local commit** were missing.

Recovery rule: **finish, do not re-run.** State it explicitly in the resume packet, because re-running
is the wrong instinct here for three reasons:

- it burns a tool window re-deriving data that is already on disk;
- for a GPU or sampling lane it can produce a **different sample**, invalidating the numbers already
  recorded and reviewed;
- the manager's own WIP snapshot (`N files / M dirty / 0 hash mismatch`) is what lets it assert
  "nothing was lost" instead of hoping.

Packet shape that worked: list every artifact already on disk **with size and mtime**, restate the
verdicts the **manager** read out of the JSON itself, name the exact remaining gap (report + commit),
and forbid re-running / re-decoding / re-rendering / GPU use in one line.

Then re-dispatch to the **same** owner session id (`--resume`), never a fresh one. And when you quote
the dead lane's verdict map, say that the manager read it from disk — that makes it manager-verified
data rather than a worker self-report, which is what keeps the packet's "already accepted" claims
honest.

## 5. Freeze boundary

An evaluator lane must read a **hash-pinned frozen subtree** captured *after* the writer exited, not a
live tree:

- freeze the media + run record + graph + frame map + pins under a dedicated frozen id, with a
  per-file hash manifest;
- a correction after a freeze means a **new freeze id**, never editing the reviewed bytes;
- verify the freeze yourself before handing it over, and hash **both** the frozen copy and its source,
  reporting drift in either direction separately;
- the leak that motivated this: an evaluator's own full-suite run **appended 25 rows to the submitted
  packet's ledger** because the ledger path fell back to a hard-coded default. The fix was to resolve
  the path at call time from a scratch-root env var and **fail closed** if it lands inside an evidence
  root; the proof was running the evaluator's full suite and showing the packet ledger's bytes, row
  count and sha **unchanged** across the run.

## 6. What the wave manager must not do

- no APPROVED / CLOSED / QUALITY_ACCEPTED — only `SUBMITTED` / `MANAGER_VERIFIED_PENDING_REVIEW`
  plus the residual gaps;
- no push, merge, reset, rebase, stash, restore or clean;
- no quality verdict on generated media from a route with no vision: `NOT_REVIEWED` stays
  `NOT_REVIEWED`, and a technical pass never becomes a quality pass;
- no self-authorising the next sprint, and no silently widening scope to "clean up" what a dead lane
  left behind.

## 7. Verification-script pitfalls hit while doing the above

- A hash-manifest re-check reported **194/194 corrupted** when every file was intact. Two bugs: it
  hashed the `src` path while the manifest stored the digest of the **frozen copy**, and the manifest
  used **UPPERCASE** hex versus lowercase `hexdigest()`. Print the manifest's own schema and one full
  sample entry first, compare lowercased, and cross-check the manifest's own `hash_mismatch` counter.
  A blanket 100 %/0 % result is a bug signal, not a finding.
- Re-using one SQLite cursor inside its own iteration silently truncated a 13-session scan to 1 → every
  match reported "UNRESOLVED". Materialise the row list first, then query inside the loop.
- A file path containing `:` (e.g. an output root named `.../outputs/x:y/`) breaks `"${t%%:*}"`-style
  bash splitting; do this kind of measurement in Python with native `C:/…` paths instead.

## 8. Verifying a "we changed exactly one variable" round

A GPU round's whole scientific value rests on that claim, so it is verified, not read. Four checks,
all run by the manager on frozen bytes:

**a. The delta, by walking both structured payloads.** Diff the new graph against the **submitted**
baseline (the frozen copy of what actually ran, not some sibling working file) and assert the diff
*set*, never the prose. A recursive walk collecting `(path, old, new)` gave exactly one entry here —
`672:587.inputs.pose_end_percent 0 → 1` — which is what makes everything else interpretable.

```python
def walk(x, y, path="", out=None):
    out = [] if out is None else out
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            walk(x.get(k), y.get(k), f"{path}.{k}", out)
    elif isinstance(x, list) and isinstance(y, list):
        for i, (a, b) in enumerate(zip(x, y)):
            walk(a, b, f"{path}[{i}]", out)
    elif x != y:
        out.append((path, x, y))
    return out
```

Also recompute the delta against the **vendor/native template** when the claim is "this restores the
documented behaviour" — here the submitted graph carried `0` where the native workflow carries `1`,
which is the mechanism story in one comparison. And state the residual you did *not* investigate
(why the baseline left the native value in the first place) as an open item rather than an inference.

**b. Measure the produced media yourself.** `ffprobe` the container and streams — geometry, frame
count, `r_frame_rate`, `time_base`, duration — and decode **both** sides of any audio claim to raw
PCM before calling it bit-identical. Report **three separate labels** that are easy to conflate:
container duration, decoded frame duration, and samples per channel. A clip that matches on
"4.0 s" in one label can carry a different number in another.

**c. Separate the deliverable from the intermediates.** Raw server outputs are not the export: here
they were 121 frames / 640×368 / no audio, plus a **2-up 1280×368 composite** sibling. A server that
emits both makes "two clips appeared" look like two submissions. Identify the candidate, say what the
sibling is, and note that the export step (drop the padding frame, crop, reattach audio) is still
owed if it has not run. Do this from the bytes, not from the worker's filenames.

**d. The shutdown proof is a two-signal claim.** Closing an engine is proven by *port state* **and**
*process state*, and one common signal is a false positive:

- `connect_ex` on a **non-blocking** socket returns **10035 (`WSAEWOULDBLOCK`)** for a closed port
  *and* for a live port that merely cannot complete immediately — it proves nothing. Probe
  **blocking** and expect **10061 (`WSAECONNREFUSED`)**. Record both values with the reason, and if a
  packet forbids the weak signal, say that you re-probed rather than reporting the first number.
- Prove the pid set: listeners after the stop = `[]`, engine pid(s) gone, and the pids stopped must
  match the engine's command line — stopping by ancestor/tree is not scoped.
- A pid that disappeared and is **not** in your stop log is a disclosure ("collateral removed by this
  stop: `<pid>`, a poll helper of the manager's own"), printed verbatim, not omitted.

**e. Throughput wording.** If accepted seconds is 0, cost per accepted second is **undefined** — do
not divide wall time by clip length and present the quotient as throughput. Report generated seconds
and accepted seconds separately, and record peak VRAM **and** peak RAM from the run's own resource
samples rather than estimating them.
