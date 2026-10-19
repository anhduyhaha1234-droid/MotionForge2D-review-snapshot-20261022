# Budget-capability audits, self-referential gates, and truthful re-statements

Session evidence: MotionForge2D MF-END-10/M1-01 (2026-09-30 → 10-01). Every claim below
was measured on disk / against installed source in that run, not theorised.

Three independent lessons, each one cost a full review round to discover.

---

## 1. "We have a budget cap" must be PROVEN per-mechanism, or it is a false claim

A reviewer rejected a submission whose report said the worker "stopped on budget".
It did not: it ended on `finish_reason=length` + truncated-arguments. Worse, the
dispatch script only measured requests **after** the run and enforced nothing but a
subprocess wall-clock timeout. Result: `BLOCKED_BUDGET_GUARD` at review.

### The audit recipe (read-only, ~0 model cost — do it BEFORE dispatch)

Ask one question: **does a supported mechanism cap cumulative OUTBOUND model
requests BEFORE the request is sent, including inner retries?** Probe each layer, and
record the file hash of everything you inspected:

| Layer | How to probe | What "absent" looks like |
|---|---|---|
| CLI top-level | `hermes --help`, regex `--[a-z-]*(request\|budget\|cap\|limit\|usage)` | only `--usage-file` (an *output* report, not a gate) |
| CLI subcommand | `hermes chat --help`, same regex | NONE — and `--max-turns` is present but is **iterations per conversation turn**, not requests |
| Config defaults | regex over `hermes_cli/config_defaults.py` for `max_api_calls\|request_budget\|budget\|max_cost` | NONE |
| Runtime identifiers | grep `agent/*.py` + `hermes_cli/*.py` for the same names | **0 files** |
| Pre-request hook | see §1a — this is the trap | event fires, but its return value is **discarded** |
| Shell hooks (`hooks:` in config) | `agent/shell_hooks.py::_parse_response` | block honoured **only** for `pre_tool_call` (+ keep-going for `pre_verify`) |
| Provider `/v1/models` | look for `rate_limit`/`quota` fields | NONE on a local router |
| `hermes egress` | CLI help | an external credential-injection proxy, not a per-run counter |
| Docs site | fetch the docs index, `grep -ci budget`; try `/docs/user-guide/budget` | 0 matches / **404** |

### 1a. The `pre_api_request` trap — fires, looks right, cannot block

`agent/conversation_loop.py` DOES fire `pre_api_request` immediately before every
provider call, and the kwargs are exactly what a limiter would need
(`api_call_count`, `retry_count`, `model`, `base_url`, `request`). It reads like the
right hook. It is not, because of one detail:

```bash
grep -cE "=\s*_invoke_hook" agent/conversation_loop.py    # → 0
```

The call site is a **bare** `_invoke_hook("pre_api_request", …)` — the result is never
assigned, so **not even a plugin** can turn it into a block. And there is no shell-hook
binding for that event at all (`VALID_HOOKS` in `hermes_cli/plugins.py` lists it, but
`_parse_response` only translates a block directive for `pre_tool_call`).

> General rule: **read the call site, not the event name.** A hook that is *fired*
> is not a hook that is *honoured*. `grep -c '= .*invoke_hook'` is the one-line test.

### 1b. Reporting discipline once a cap is found missing

- **`BLOCKED_BUDGET_GUARD`, stop before dispatch.** Do not invent a CLI flag, do not
  build a wrapper subsystem, do not edit global config to fake one — the packet
  forbade all three, and a post-hoc count cannot provide the guarantee a pre-request
  cap provides.
- **Report attempt counts, not just accounted calls.** Provider-truncated /
  partial-stream responses are retried or returned by the runtime **before** usage
  accounting, so they never reach the DB. Measured: 114 accounted + **30 unaccounted**
  = **≥144 attempts** against a cap of 60. The undercount was 26 %.
- **Never merge incomparable counters into one "total".** Loop/API counters
  (442), background counters (24), manual route probes (2), accounted calls (114) and
  unaccounted attempts (30) stay in **separate rows**. If an exact HTTP total is
  unrecoverable, the honest value is `unavailable`.
- **A DB row reading `api_call_count=0` with 286 assistant messages is MISSING
  TELEMETRY, not zero usage.** Say so; never let a 0 imply "cheap".

---

## 2. A gate that checks artifacts written AFTER it, or a manifest that hashes itself, fails forever

The previous round produced four consecutive gate failures that were **all gate bugs,
never artifact bugs**. Each is now a reusable pitfall:

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | row FAILs with an **empty** actual | PowerShell `(… ).Count` returns nothing when the filter yields a single object (not a collection) | count in Python/`psutil`, or normalise with `@(...)` |
| 2 | "no worker process" row FAILs with `actual=1` | the checker passed the session id **inline in its own argv** (`python -c "…20260928_181955_a6d89a…"`) so it matched **itself** | read the id from a **file**; exclude self + ancestors + shell wrappers by pid/name (`scripts/` recipe below) |
| 3 | ledger row FAILs `expected=10 actual=12` | expectation was the **literal count** of an **append-only** ledger | assert the *property* (`≥ floor`), never a frozen count |
| 4 | manifest self-check reports N entries `CHANGED` | the manifest hashed files that **carry the manifest's own digest** (`*_seal.txt` recording the digest, and the gate file written after the build) | **exclude exactly the self-referential files** from enumeration; prove determinism by running the builder **twice** and comparing `entries_digest` |

### The order that makes it stop

```
1. run the gate             → writes gate output
2. run the manifest builder → LAST write into the evidence root
3. verify READ-ONLY         → prints mismatch:[], unlisted_on_disk:[]
```

Any file written into the root **after** step 2 invalidates it. Keep the gate's own
output and the manifest in the exclusion set, and never assert on them.

### Reporting rule

Preserve **every** failing raw run (`T015`, `T019`, `T020`, `T021` style files) and
name them in the report. Do **not** edit a number so a check agrees. A gate that had
to be fixed 4× is itself evidence about the gate, and a reviewer needs to see it.

---

## 3. Correcting a false report WITHOUT rewriting history

When review finds false claims in an **already-submitted** round, do not edit the old
artifacts. Write an **additive** `TRUTH_CORRECTION.md` that names each false claim,
states the truth beside it, and cites the source line. The old bytes stay as they were
— that is what makes the correction auditable instead of invisible.

Structure that worked (6 rows measured):

| # | Prior claim | Truth | Source |
|---|---|---|---|
| A1 | "the cap was reached, so the writer stopped safely" | no budget-stop event exists; `timed_out=false`, `exit_code=0`, ended on truncated args | worker log tail + receipt |
| A2 | "enforcement actually applied … a watchdog" | post-hoc count + 7200 s timeout only | dispatch script lines |
| A3 | counts presented as the total | 114 accounted **+ 30 unaccounted** = ≥144 | reviewer usage audit |
| A4 | manager "well under 20" | 442 main + 24 background counters | exact-session log |
| A5 | three byte counts | 37,380 / 14,636 / 22,218 (SHAs were right) | re-measured |
| A6 | AC rows marked PASS | not covered; independent probes disprove them | reviewer adversarial result |

Two rules learned here:

- **Attribute authorship per artifact.** Manager-measured numbers must not be written
  as if the worker produced them, and vice versa. State the author in every file.
- **"Manifest intact" ≠ "conclusions correct".** 154/154 entries hashed clean while
  the document's prose was wrong. Verify claims, not just bytes.

---

## 4. Build-gate honesty (don't rename an alternative as the default PASS)

Measured: `npm run build` → Turbopack `FATAL: Symlink [project]/node_modules is
invalid, it points out of the filesystem root`, because `node_modules` was a Windows
**junction** to an external installed tree. `npx next build --webpack` → **RC=0**, all
routes generated.

Rules:

- Report the **standard** command's failure and the **alternative**'s result as two
  separate facts. Never present the alternative's green as "the default build passes".
- The junction itself is a harness convenience (avoids `npm install`); it is not a
  product defect — but say which one it is and let the reviewer rule.
- Bonus, measured: removing a Windows **junction** with `shutil.rmtree` deletes only
  the link; the **target tree stays intact** (verified: 297 packages still present in
  the source tree afterwards). Safe cleanup pattern for disposable verifier worktrees —
  but still verify the target after removal, because a real directory would have been
  deleted.

---

## 5. Candidate hygiene when a worker dies mid-closing

A worker can exit `exit=0` with the work **done but uncommitted**, having run out of
output budget. Before deciding anything:

1. `git status --porcelain` in the task worktree (list M / ??).
2. Re-run the task's own tests yourself — measured **4 passed** on the frozen spec.
3. Byte-for-byte backup the dirty candidate **before** touching anything, and
   re-verify the backup hashes at the *end* of the round too (proves nothing drifted).

Then: the candidate is validated as **bytes on disk** with hashes, not as a commit —
and the report must say so in those words. Whether a finishing-only resume is allowed
is a reviewer decision, not yours to assume.

Related: this same round's **base control** (run the candidate's own spec against a
pre-patch worktree at the same base, same API, identical spec bytes) is what turns
"the test passes" into "the test is revert-sensitive": candidate **4 passed** / base
**4 failed**. A green spec alone proves nothing about what it would catch.
