# Budget reporting as a Manager: enforced vs observed, and stop rules

Measured 2026-10-01 (MotionForge M1-01 correction, two consecutive rounds). A submission
was rejected by an independent reviewer on **budget reporting alone** — while the product
work was still in scope — and the same reviewer then withdrew the precondition it had set,
because the precondition was impossible to satisfy. Both halves are reusable Manager
discipline.

## 1. Every budget number is one of two classes — label it

| Class | Meaning | How to report it |
|---|---|---|
| **ENFORCED** | a real argv flag or a launcher timeout | the value **and** its proof: receipt field / argv element / source line |
| **OBSERVED** | a threshold compared against a count you compute, whose telemetry can lag | "operating budget, observed" + an explicit *"this is not a hard cap"* |

Enforced facts that are easy to prove and worth pinning in the receipt:

- `--max-turns N` → `receipt.max_turns == "N"` **and** the argv recorded in the receipt.
- `DEADLINE_SECONDS = 7200` → the launcher's `subprocess.run(..., timeout=…)` plus
  `receipt.deadline_seconds`.
- "one dispatch only" → the absence of any relaunch path in the harness, stated as such.

**The caveat that must accompany `--max-turns`:**

> `--max-turns` bounds **tool-calling iterations inside one conversation turn**. It is
> **not** a cumulative outbound-request count and does not cover every auxiliary call.

Disclose auxiliary consumers rather than hiding them: recovery **iteration refunds**, a
**final-summary** call after the iteration budget is exhausted, and a **separate
background-review budget** (measured: 16 iterations). If no narrow switch disables an
auxiliary, say so and record its usage in its **own** ledger row — never change global
config/profile just to make a total look tidy.

## 2. The false-comfort pattern that got a whole submission rejected

Two claims, both contradicted by the exact-session log:

- *"Manager was well under [20] requests"* — the log recorded main loop/API counters
  **300 + 142**, plus background counters **8 + 16**.
- *"the worker reached the cap, so it stopped safely"* — the raw log ended on repeated
  truncation retries, the receipt said `timed_out=false, exit_code=0`, and **no budget-stop
  event existed anywhere**.

Rules:

1. **Never attribute a stop to a budget without a budget-stop event in the artifact.** Read
   the log tail; the true cause (output truncation, transport flap, quota) is stated there.
2. **Do not sum unlike counters into one "exact HTTP total".** Loop/API counters,
   background counters, approval calls and route probes are different kinds. Keep separate
   rows; write `unavailable` for the total when it is unavailable.
3. **`0` in the usage DB is missing telemetry, not zero usage.** A session row with
   `api_call_count=0` beside hundreds of real messages means the counter was never written.
4. **Manager reasoning between tool calls is Manager usage.** Running read-only CLI/shell
   commands does **not** make Manager usage zero.
5. **Undercounted attempts are normal.** Attempts the runtime retries/returns *before*
   usage accounting never reach the DB — measured **114 accounted + 30 unaccounted ⇒ ≥144**
   against a declared cap of 60. Report the buckets separately and use "≥ N" when only a
   lower bound is provable.
6. **New allowance is additive.** Never reset or relabel historical cost; the prior overrun
   stays on the record.

## 3. When the reviewer withdraws its own precondition: SUPERSEDE, never PASS

A reviewer had required proof of a hard pre-request HTTP limiter before any correction. The
capability does not exist (see the capability-audit table below), so the reviewer replaced
it with an **operational** criterion and marked the old one
**`SUPERSEDED_FOR_THIS_CORRECTION`**.

- Record the new criterion; mark the old one **superseded** — explicitly **not PASS**.
  A withdrawn condition is not a satisfied one.
- Keep the original finding as **historical fact**. Do not retract "this was never enforced
  and was misreported" just because the requirement was dropped.
- Add one table: which concerns the replacement now covers, and which no longer apply.

## 4. Prove a capability is ABSENT before escalating — as a checkable table

Before raising "the mechanism does not exist", produce an audit a reviewer can verify:

| Mechanism probed | Finding |
|---|---|
| CLI `--help` for the relevant flags | only an output-reporting flag; no gate |
| config defaults | no key of that class |
| runtime identifiers grepped across agent/CLI source | **0 files** |
| the hook that fires before the call | fires, **but the return value is discarded** (`grep -c '= _invoke_hook'` = **0**) ⇒ not even a plugin can block |
| shell-hook events | block directives honoured for one event only; the needed one has no block path |
| provider `/v1/models` | no rate-limit/quota metadata field |
| docs site | page returns **404**; term appears 0 times in the index |

Record the **sha256** of every file inspected so the claim is auditable. Escalating with
this table is cheap and defensible; "I could not find it" is neither.

## 5. Stop rules that outrank a larger budget

- **Two identical failures with no code/evidence delta ⇒ stop at a safe boundary and submit
  PARTIAL**, even with budget unspent. Verify the delta first (`sha256` of the write-set
  before vs after); `delta_files == 0` is what makes the rule applicable.
- A **bigger budget does not fix a deterministic ceiling.** When the failure is structural
  (one monolithic `write_file` exceeding the per-response output cap), extra attempts buy
  more identical failures.
- Quota / auth / config failure → **hard stop**, no fallback.
- **One dispatch per correction.** No relaunch to reset a loop or a time cap.
- When the fix lies **outside** the task's write-set, do not spend another round silently —
  name it as the decision the reviewer must make.
- Waiting on a review is spent with **zero model calls**: use non-LLM process waits, never
  model-polling, and never generate tokens to re-polish report formatting.
