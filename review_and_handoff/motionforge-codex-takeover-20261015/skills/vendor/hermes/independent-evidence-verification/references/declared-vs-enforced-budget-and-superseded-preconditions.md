# Declaring a budget: enforced vs observed, and superseded preconditions

Measured 2026-10-01 (MotionForge M1-01). A reviewer rejected a whole submission on
**budget reporting alone** — not on the product — and then removed the precondition it had
set, because the precondition was unsatisfiable. Both halves of that exchange are reusable.

## 1. Separate ENFORCED from OBSERVED, in writing, every time

A budget claim is only honest if the reader can tell which numbers are mechanically
guaranteed and which are stop-rules on a count you compute after the fact.

| Class | Means | How to state it |
|---|---|---|
| **ENFORCED** | a flag/deadline in the real argv, or a timeout in the launcher's code | quote the value **and** its proof: the receipt field, the argv element, the source line |
| **OBSERVED** | a threshold you compare a *measured* count against, whose telemetry can lag | say "operating budget, observed" and add that it is **not** a hard cap |

Worked example of the enforced side:

- `--max-turns 120` — proven by the real argv and by `receipt.max_turns == "120"`.
- `DEADLINE_SECONDS = 7200` — proven by `subprocess.run(..., timeout=…)` and
  `receipt.deadline_seconds`.
- one dispatch only — proven by the absence of any relaunch path in the harness.

And the honest caveat that must accompany a `--max-turns` number:

> `--max-turns` bounds **tool-calling iterations inside one conversation turn**. It is
> **not** a cumulative outbound-request count and does **not** cover every auxiliary call.

Known auxiliary consumers to disclose rather than hide: **recovery iteration refunds**, a
**final-summary** call after the iteration budget is exhausted, and a **separate
background-review budget** (measured: 16 iterations). Cite the source lines when you can.
If no narrow switch exists to disable an auxiliary, say so and record its usage
**separately** — do **not** change global config/profile to make a number look tidy.

## 2. A false "well under budget" claim is worse than an honest overrun

Rejected pattern, verbatim from the review:

- `manager/NEXT_CODEX_REVIEW.md` claimed the manager was "well under [20]" while the
  exact-session log recorded main loop/API counters **300 + 142 = 442** plus background
  counters **8 + 16 = 24**.
- The worker stop was described as "reaching the cap, so it stopped safely" while the raw
  log ended on repeated truncation retries and the receipt said `timed_out=false,
  exit_code=0` — **no budget-stop event existed at all**.

Rules that follow:

1. **Never attribute a stop to a budget unless a budget-stop event is in the artifact.**
   Read the log tail; the real cause (truncation, transport flap, quota) is stated there.
2. **Do not sum incomparable counters into a single "exact HTTP total".** Loop/API
   counters, background counters, approval calls and route probes are **different kinds**.
   Keep them in separate rows and mark the exact total `unavailable` when it is.
3. **`0` in the DB is missing telemetry, not zero usage.** A session row with
   `api_call_count=0` beside hundreds of real messages/tool rows means the counters were
   never written. Write `unavailable` — never `0`.
4. **Manager reasoning between tool calls counts as Manager usage.** Driving read-only CLI
   or shell commands does *not* make Manager usage zero.
5. **Undercounted attempts are the norm, not an edge case.** Attempts that the runtime
   retries/returns **before** usage accounting never reach the DB. Measured: 114 accounted
   + **30 unaccounted** truncated/partial attempts ⇒ observed **≥144** against a declared
   cap of 60. Report the accounted and unaccounted buckets separately; use "≥ N" when only
   a lower bound is provable.
6. Do not relabel or reset historical cost. A new allowance is **additive**; prior
   overruns stay on the record.

## 3. When a reviewer removes its own precondition, supersede — never "PASS"

A reviewer had set a precondition ("prove a hard pre-request HTTP limiter before any
correction"). It was **unsatisfiable** — measured: no such runtime feature exists — and the
reviewer then withdrew it as **`SUPERSEDED_FOR_THIS_CORRECTION`**.

How to handle that correctly:

- Record the new acceptance criterion (here an *operational* one) and mark the old one
  **superseded**, explicitly **not PASS**. A superseded condition is not a satisfied one.
- Keep the original finding as **historical fact**. Do not retract the earlier "this was
  not enforced and was misreported" finding when the requirement is dropped.
- State plainly, in one table, which of the old condition's concerns are now covered by
  the replacement and which simply no longer apply.

## 4. Prove a capability is ABSENT before escalating, and report it as a table

Before raising a blocker of the form "the mechanism does not exist", produce an audit that
a reviewer can check line by line. The shape that worked:

| Mechanism probed | Finding |
|---|---|
| CLI `--help` for the relevant flags | only an output-reporting flag; no gate |
| config defaults | no key of that class |
| runtime identifiers grepped across the agent/CLI source | **0 files** |
| the hook that fires before the call | fires, **but** the return value is **discarded** (`grep -c '= _invoke_hook'` = **0**) ⇒ not even a plugin can block |
| shell-hook events | block directives honoured for only one event; the one you need has **no** block path |
| provider `/v1/models` | no rate-limit/quota metadata field |
| docs site | the page returns **404**; the term appears 0 times in the index |

Escalating with this table is cheap and defensible; escalating with "I could not find it"
is neither. Include the **hashes** of every file you inspected so the claim is auditable.
