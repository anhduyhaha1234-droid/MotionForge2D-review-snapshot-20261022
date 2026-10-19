# Multi-lane dispatch resilience (measured 2026-09-23, MotionForge2D core/tool wave)

Seven lanes were dispatched in one wave, killed twice by upstream 502 flaps, and all
recovered. Every rule below was paid for with a real defect; the numbers are from that run.

## 1. Lane identity must be provable — one packet file per lane per round

A `--resume` continuation id **does not track dispatch order**, and two sessions can share
the same start second, so pairing `parent -> actual` by "batch order, then created_at" got
**4 of 6 wrong**.

- **Give every lane its own packet file**, one per round, even when the content is 95 %
  identical. That makes `first user message == packet head` a valid proof.
- With ONE merged packet ("read the section matching your Task ID") the mapping becomes
  **unprovable**: all lanes' first user message is byte-identical, and this Hermes `state.db`
  stores **no resume parent** (`parent_session_id`, `cwd`, `title` all NULL for worker rows).
  Do not burn time proving it — record the row as **INFERRED** (dispatch order + stagger
  timestamps) in a `actual_session_proven_by` field and move on.
- Dead ends confirmed this run, so do not retry them: tool-RESULT keyword counts (results echo
  the packet text), `[terminal] ran \`...\`` echoes (a UI rendering, not stored in the DB),
  `parent_session_id` lineage.
- **Ask the worker to report its own id**: a worker that reads `HERMES_SESSION_ID` from its own
  process env confirms the mapping. One lane did exactly this and turned its INFERRED row into
  CONFIRMED — cheap and decisive. Put that request in the packet.
- Fix at the source: one lane per packet per round beats any clever reconstruction.

## 2. A CLI launcher's `exit 0` says nothing — gate on the log payload

Three separate times in one run the launcher returned **exit 0** while its ~125-byte log held
only `API call failed after 3 retries: HTTP 503: ... [502]: fetch connect timeout`. Six of
seven lanes "exited normally" having done nothing. Classify as a **transient upstream failure**
(`RUNNING_RETRY_WAIT`), not a task result: keep the payload as evidence, then wait ~5 min,
re-probe the route (`/models` 200 is NOT proof — do a real chat probe and check it returns
content), and resume the **same owner/model/scope**.

## 3. Flap budget: reduce concurrency, stagger, snapshot before re-dispatch

- Two flaps inside ~50 minutes with 7 streams open. Recovery that held: **cut to 3 concurrent
  streams** and **stagger starts by 45 s**. No flap after that.
- Before re-dispatching any lane, measure what the dead round left on disk and **snapshot it**
  (`git status --porcelain`, dirty-file count, per-file sha). Lanes that died before writing
  should be told so plainly; lanes that died mid-write must be told "your work is on disk,
  verify then finish".
- A crashed writer can leave **untracked code that never executed**. Treat it as unexecuted:
  compile it, lint it, then **run it**. In this run a 1,152-line module left behind by a crash
  raised on every call (a request-model field mismatch with `extra="forbid"`), so a core path
  had never once run despite the file existing. "The file exists" is not evidence.

## 4. Freeze before the evaluator reads, and prove the sentinel

- The evaluator reads **only** a hash-pinned frozen copy, created **after** the writer's session
  went terminal. A new candidate ⇒ a **new freeze id**; never edit inside an existing freeze.
- Freeze manifest must record per-file hash **and** the real source path. See
  `references/`-adjacent note: an integrity re-check that hashes the wrong column or compares
  UPPERCASE hex to lowercase `hexdigest()` reports 100 % corruption on intact files — print the
  manifest's own schema and one sample row before declaring a failure, and cross-check the
  manifest's own `hash_mismatch` counter. A blanket 100 %/0 % result is a bug signal.
- **Sentinel (zero-append proof):** run the full suite yourself and assert a protected evidence
  ledger's `size + rows + sha256` are **identical before and after**. This run: 184,680 B /
  422 rows / sha `21d5b178...` unchanged, with the original 173,959-byte prefix still hashing to
  `ed95c099...`. Prior art: a ledger opened with mode `"w"` once truncated 306 rows to 20 and the
  bytes were unrecoverable — so a fix for that class needs a sentinel, not a test.

## 5. Prompt hygiene that prevented real bugs

- **Never re-use a bare path alias as a path segment.** Packets defined `**NEW:** <run-root>`
  then said "write under `NEW/<TASK>/**`". Two of seven lanes read `NEW` as a folder to create
  and wrote to `<run-root>/NEW/<TASK>/...`; five wrote `<run-root>/<TASK>/...`. Both contained
  hashed artifacts. Spell the literal destination or give a worked example.
- **Once bytes are hashed, never move them to "tidy up".** Record the real path in the manifest
  and registry so a reviewer can recompute the hash; the path is data, not a mistake to hide.
- State the literal path for anything a worker must read, and forbid whole-tree walks
  (`find` over a large runtime tree timed out at 300 s) — ask for narrow, targeted locates.
- Put "report the exact remaining gap, `RUNNING`, not `TASK_SUBMITTED`" in every packet. The
  honest partial reports this run (a lane out of tool budget listing 13/14 done) were more
  useful than a padded green.

## 6. The Manager's own documents are artifacts too

- Fuzzy `patch` on a markdown **table** silently deleted a whole row and doubled the leading
  `|` while reporting success three times in a row. **Rewrite the whole table or the whole
  document** when editing adjacent rows, and make the final gate assert row counts and that no
  line starts with `||`.
- An append-only manager ledger accumulates **duplicates** when you backfill earlier rounds.
  Never rewrite raw history: emit `dispatch-ledger.reconciled.jsonl` + a reconciliation note,
  prove `receipt files on disk == dispatches`, and record a killed pre-write dispatch explicitly
  (`receipt: null, outcome: KILLED_PRE_WRITE`) instead of dropping the row.
- Run the final gate **against your own outputs** — it caught two of the Manager's own errors
  (corrupted registry, wrong resume pairing) which no worker report would have surfaced.

## 7. Heavy-GPU lane discipline

- One heavy GPU job at a time: before dispatch, assert the GPU is idle **and** no engine port is
  listening; after the round, prove shutdown by **blocking** connect → `10061 WSAECONNREFUSED`.
  A non-blocking socket's `10035 WSAEWOULDBLOCK` is not evidence of a closed port, and a worker
  correctly refused it.
- Expect **two sampler passes per prompt** from some ComfyUI video templates (an s1+s2 loop). Do
  not read "2 passes / 2 output files" as a duplicate submit — verify with the prompt id and the
  server's own `got prompt` / `Prompt executed` counts before accusing the worker. A cross-check
  that "4 executed <-> 4 stage lines" looked like 1:1 but was a 2x2 coincidence; only reading
  per-prompt did the counts resolve.
- Separate **server time / wait / wall** and keep `accepted seconds = 0` explicit: with zero
  accepted output, **cost per accepted second is undefined** — do not divide wall by duration and
  present it as throughput.

## 8. Reporting shape the user expects (Vietnamese, always)

Lead with status, then a table of real numbers (hashes, counts, ports, timings), then an ETA
table anchored to the date in `+07`, and disclose the Manager's own mistakes explicitly rather
than burying them. When the user asks "bao giờ xong", answer with the ETA table plus the single
remaining item that only they can unblock (here: a human must watch the clip — the route has no
vision, so no self-reported visual PASS is allowed). Never self-approve, self-close, push, or
open the next sprint.
