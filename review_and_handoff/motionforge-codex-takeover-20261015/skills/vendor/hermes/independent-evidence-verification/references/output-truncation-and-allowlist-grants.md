# When a round cannot simply continue: output truncation, and files no allowlist covers

Two situations measured 2026-09-29 (MF2D CMC correction round) where "resume and keep
going" is the WRONG instinct. Both were verified on disk.

> **Addendum measured 2026-10-01 — the repetition rule beats the budget rule.**
> A correction round was dispatched with a generous operating budget (200 observed
> attempts) and a 7200 s deadline. The worker returned `exit 0` after **2 m 30 s** having
> touched **zero bytes** — same terminal signature as the previous round:
> `finish_reason='length'` ×5 → truncated tool args ×4 → *"refusing to execute incomplete
> tool arguments"*. Because the signature **repeated with no code/evidence delta**, the
> correct action was to **stop and submit PARTIAL**, not to spend the remaining budget:
> the package's own rule was *"two identical failures with no code/evidence delta ⇒ stop
> immediately, even with budget left."*
>
> Two things to carry forward from that:
> 1. **A big budget does not fix a deterministic ceiling.** When the failure mode is
>    structural (one monolithic `write_file` exceeding the per-response output cap), more
>    attempts buy more identical failures. Verify the delta first (`sha256` of the
>    write-set before vs after); `delta_files == 0` is what makes the repetition rule
>    applicable.
> 2. **Diagnose the ceiling, don't blame quota or budget.** Grep the log for quota and
>    transport markers — measured `0` × `503`, `0` × `502`, `0` × `UsageLimit` — and read
>    the provider's advertised limits (`/v1/models`: `max_completion_tokens`, `context_length`).
>    That turns "the worker died" into a precise statement: *the per-response output cap
>    met one oversized tool payload, and the refuse-incomplete-arguments guard fired
>    correctly.* The remedy then belongs to whoever can change the write discipline or the
>    ceiling — which may be **outside** the task's write-set, so name it as the decision the
>    reviewer must make instead of silently spending another round.

## 1. Output-token truncation mid-`patch` — distinct from the iteration cap

The documented budget-exhaustion mode is the TOOL-CALL iteration cap
(`Iteration budget reached (160/160)`, see
`iteration-budget-exhaustion-and-finish-packets.md`). This is a **different** ceiling:
the per-response OUTPUT token limit, which bites mid-tool-call.

Signature (verbatim from the lane log):

```
┊ 🔧 preparing patch…
⚠️  Response truncated (finish_reason='length') - model hit max output tokens
   … x5 …
⚠️  Truncated tool call detected — retrying API call (1/4)...
⚠️  Truncated tool call response detected again — refusing to execute incomplete
   tool arguments.
 ─  ⚕ Hermes ─
 Response truncated due to output length limit
Resume this session with:  hermes --resume <session>
```

The launcher still returned **`exit=0`**, wall time ~10 min, and the session banner
looked like a normal end. Nothing about it says "incomplete".

**Two distinct triggers — identify which one you have before prescribing a fix.**

**(a) One oversized `patch`.** The model composes a single very large patch. Five
consecutive attempts truncate at the same point, the retry ladder exhausts, and the
runtime correctly **refuses to execute incomplete tool arguments**. That refusal is the
desired safety behaviour — it is NOT a lane failure, NOT a bad patch, and NOT a signal
the work was wrong. Fix with the size discipline below.

**(b) An investigation loop — the one that survives the size discipline.** Measured
2026-09-29 in the SAME round, after the size rule had already been issued: a lane
truncated on **three consecutive resumes** without landing a byte between round 1 and
round 2 (`porcelain` unchanged). Reading the prompt-echo tail shows what actually ate the
output budget — not a patch at all:

```
┊ 📖 preparing read_file…
⚠️  Response truncated (finish_reason='length') - model hit max output tokens   (x5)
```

The lane was burning its whole response budget on reasoning + exploratory
`grep`/`read_file` calls trying to work out *how to build a valid test fixture*, and died
at the point where it ran out of output tokens composing the next probe. A worker stuck
in this loop will keep re-deriving the same missing knowledge every resume, so the
≤60-lines-per-patch rule does **not** help — the patch was never the problem.

### Recovery recipe

1. **Do not trust exit=0 — measure the disk.** Check `git status --porcelain`,
   `git diff --numstat`, and whether the evidence dir has more than `TARGET.md`.
2. **Validate what DID land before resuming**, so the next round does not build on a
   half-written file. Run **all three** checks — each one catches a different class of
   damage, and the cheapest one alone is a trap:

   **(a) Syntax — necessary, NOT sufficient.** `python -B -m py_compile <file>` → rc 0.
   A truncated `patch` can land **syntactically valid but structurally wrong** code, so
   this check passing means nothing on its own (see (c)).
   **(b) Behaviour — run the lane's own focused test file.**
   `python -B -m pytest <the task's test file> -q -p no:cacheprovider` and **compare
   against the pre-round baseline**. This is the check that actually finds truncation
   damage.
   **(c) Structure — AST, when the patch inserted functions.**
   A truncated patch can splice new `def`s into the *wrong scope*: dedented one level
   short, they nest inside the preceding function instead of landing at module level.
   The file still compiles, imports, and looks right in a diff.

   Measured 2026-09-29 (MF2D C19): `py_compile` returned **rc 0** while the lane's test
   file was **`13 failed, 19 passed`** — the pre-round suite had been green. AST output
   showed the real damage:

   ```
   MODULE_LEVEL_FUNCS 16
   NESTED_INSIDE _graph_object_sha256 = ['_canonical_json', 's10_unit_prompt_sha256',
       's10_window_basename', 's10_unit_control', 's10_unit_time_map', 's10_unit_binding_digest']
   _graph_object_sha256 spans lines 394..507
   ```

   A `canonical = json.dumps(...)` one-liner had been replaced by `def _canonical_json(...)`
   and five sibling `def`s were appended **at the same indent**, so six functions became
   inner functions and the host body was left with `return hashlib.sha256(canonical.encode(...))`
   referencing a name that no longer existed → `NameError: name 'canonical' is not defined`
   at the host's final line, reddening 8 tests.

   Run `scripts/verify_patch_structure.py <file> [--expect-toplevel NAME …]` — it parses
   the AST, lists module-level defs, and reports any unexpected nesting.

   **The general rule: a truncated patch is a candidate REGRESSION, not merely an
   incomplete edit.** The refusal to execute incomplete arguments protects you from
   *garbage* input, not from a *valid-looking half-application*. Never resume onto bytes
   whose test suite you have not re-run.

   - `grep -n` for the specific wiring/call sites the patch was supposed to add — prove
     the *behavioural* edit is present, not just that lines were added.
   In the measured GOOD case the lane had landed **372 real lines** and the wiring calls
   (`_zo.compare_occlusion_facts`, `_tr.compare_motion_facts`) were already present and
   live — real progress, only the last patch lost.

   **Two outcomes, two packet types.** If the landed bytes pass (b)+(c), send a *finishing*
   packet ("do not rebuild"). If they FAIL — as C19 did — the packet must be a *repair*
   packet that (i) names the exact defect with its measured evidence (AST nesting list,
   the failing tests, the `NameError` and its line), (ii) forbids further investigation,
   and (iii) **forbids committing until the suite is green**, so a broken tree is never
   blessed with a commit. Snapshot first either way; the repair round is the case where a
   later destructive write costs the entire task.
3. **Resume the SAME session with a finishing packet**, and open it by telling the
   worker explicitly that the previous round did **not fail** and its landed work was
   verified — quoting the Manager's own measurements (diff numstat, py_compile,
   the grep hits). Otherwise the resumed agent re-reads and redoes its own work.
4. Put a **size discipline** in the packet (see below) or it will truncate again.
5. **If it truncates a SECOND time, stop prescribing and go do the reconnaissance
   yourself** (see the next section). Do not issue a third "try again, smaller" packet.

### The escalation that actually breaks the loop: Manager does the reconnaissance

The ≤60-lines-per-patch rule failed to stop trigger (b) on three attempts. What stopped
it was the Manager **pre-diagnosing the lane's open question to disk truth** and shipping
the answers inside the next packet:

1. **Reproduce the blocker first-hand, as the Manager.** Run the lane's own test file and
   read the actual failure output — do not infer it from the worker's reasoning trace.
   This is cheap and it is ground truth: measured, the lane's *new* tests were genuinely
   red (`3 failed, 40 passed`) while all 40 pre-existing tests were green, and the three
   failures had three different causes, each pinned to a file+line.
2. **Resolve every ambiguity the worker was burning budget on**, then write them into the
   packet as flat statements: exact git state, exact test pass/fail counts, the real list
   of routes/paths, *how to read them correctly*, the cause of each failure, and the
   specific fix for each.
3. **Forbid further investigation in the packet, explicitly and as a numbered rule:**
   "no `grep`/`read` to learn more — everything needed is in this packet"; "no new
   probe/script", restrict the allowed verbs (patch / test / git only).

   **Do NOT expect `--max-turns` to fix this.** The iteration cap and the output-token
   cap are orthogonal: `--max-turns` bounds how many agent iterations a turn may take,
   while the truncation is a per-RESPONSE output ceiling. Measured in the same round, a
   lane truncated at `--max-turns 80` and the next resume at `--max-turns 60` succeeded
   — but the lever that changed was the recon packet, not the cap. Lowering the cap is
   still worth doing for cost control, but a packet that says "reduced max-turns" and
   nothing else will truncate again.
4. **Demand commit-early ordering**, so a later truncation cannot destroy a whole round:
   "patch → test → when green, COMMIT IMMEDIATELY as one command → then report." State
   that committing a partially-green tree is acceptable *provided* the report labels the
   still-red test honestly. Never let a lane end with valid uncommitted bytes.

   **Gate commit-early on the suite, not on the diff.** The rule above is "commit when
   green", and a truncated lane will happily read it as "commit now". Measured C19: the
   damaged tree (13 red tests) sat **uncommitted** while the good lanes committed — which
   is the right outcome, and it happened only because the packet named a blocking test
   command. Always phrase it as `test == green → commit` with the exact command, and add a
   line for the failure branch: *"if the suite is still red when budget runs out, do NOT
   commit; write the remaining failures into FINDINGS.md and stop `BLOCKED`. The bytes are
   snapshotted, so nothing is lost."* A broken tree that gets committed is far more
   expensive than a dirty tree that gets resumed.

A diagnostic clue worth checking: **cost per call**. A lane hitting the investigation loop
shows a wildly inflated uncached-input figure for the tool calls it completes — measured,
43 calls / 522K uncached for a *smaller* job, versus 45K uncached for a sibling lane that
did a larger one. When one lane's uncached-per-call is an order of magnitude above its
peers, suspect the loop rather than a hard task.

**Protect the bytes before you resume.** Snapshot the uncommitted working files into the
run's evidence tree and verify the hashes match the worktree byte-for-byte, then state the
hashes in the packet. A lane that must be resumed repeatedly is exactly the case where a
later destructive write would cost the whole round.

```bash
mkdir -p <run>/manager/snapshots/<lane>_uncommitted
cd <worktree> && cp -p <each patched file> <snap>/
sha256sum <snap>/*   # must equal sha256sum of the same paths in the worktree
```

Snapshot even when the files are *tracked-and-modified* (restorable from git with effort):
`git stash`/`checkout` are banned by the standing Git rules, so a plain byte copy is the
only sanctioned safety net inside the round.

### Cost the loop, and put the number in the incident record

The investigation loop shows up as an inflated **uncached input per call**, so a
per-task usage ledger makes it measurable instead of anecdotal. Measured in one round:

| Lane | calls | uncached input | output |
|---|---:|---:|---:|
| sibling doing a LARGER job | 61 | 45,730 | 40,989 |
| lane in the truncation loop | 43 | **522,454** | 74,878 |

Same-order output, **11× the uncached input, on fewer calls** — the loop re-sends context
to re-derive knowledge it never stores. When one lane's uncached-per-call is an order of
magnitude above its peers, suspect the loop before suspecting a hard task, and quote the
table in the incident report so the process fix has a number attached.

### The finishing packet must not read as "do it again"

A resume packet that opens with the task contract re-stated invites the worker to redo
work it already landed. State, in this order: (1) the previous round **did not fail**;
(2) the Manager's own measurements of what is already on disk (numstat, `py_compile` rc,
the specific wiring/call sites grepped); (3) "finish, do not rebuild"; (4) only then the
remaining steps. Measured: a lane that had already landed 372 correct lines plus the live
wiring calls needed exactly this framing to stop re-deriving and commit.

### Prevention — put this in every large-edit packet

- **≤60 added lines per `patch` call.** If more is needed, split into N sequential
  patches, each with a small unique anchor.
- **Never re-paste already-landed code.** The resumed agent must patch only the gap.
  State the measured diff size so it knows what "already there" means.
- **Prefer `write_file` for NEW files under ~80 lines** — no preimage, no patch ceiling.
  **But cap it:** a *long* new file written through `write_file` re-creates trigger (b)
  (measured: a lane re-wrote an ~80-line debug probe several times and never touched the
  product code). If a new file must be large, generate it in bounded pieces, and never
  iterate on a throwaway probe — replace it with one-line `python -c` checks (≤12 lines)
  or shell one-liners.
- If a patch truncates **again**, halve it — do not retry the same payload. If it
  truncates a **third** time on the same approach, stop the approach entirely and take
  over the reconnaissance (escalation section above).
- Keep `git diff --numstat` + `py_compile` after every patch, and stop on an anomalous
  line delta (same destructive-shrink discipline as the byte guard).

## 2. A finding whose fix-file is in NO granted allowlist → request the grant, do not route it

Measured: a P1 blocker needed an edit to a file that appeared in **none** of the
allowlists granted for the round (checked task by task: the C26 allowlist, the F7
delta's diff, the QC lane's allowlist, the packaging lane's allowlist — all absent).

The tempting move — hand it to the nearest plausibly-related owner — is **scope
expansion by guessing**, and it violates the standing "do not widen the allowlist by
inference" rule. A writer handed an out-of-scope file either refuses (wasted round) or
edits outside its scope (a scope incident).

### The pattern instead

1. **Prove the gap.** Diff the finding's required file against every allowlist actually
   granted, and record the table: task → allowlist → present/absent. This table is the
   evidence; "it isn't in there" is not.
2. **Find the file's real lineage** to name a credible owner:
   `git log --format='%h %s' -- <file> | head` — the commits naming the historical lane
   tell you which owner lineage the file belongs to (measured: the file traced to a
   much older validation lane, not to any lane running in this round).
3. **Write an ALLOWLIST_GRANT_REQUEST artifact** containing:
   - the per-task allowlist-absence table from step 1;
   - the **complete micro-repro**, so the fix needs no expensive re-run — in the
     measured case: the failing run/job ids, an independent lag-scan showing the
     artifact was correct, the exact function+line of the defective comparison, and the
     already-produced candidate artifact + its sha, with an explicit
     "no re-render required" line;
   - **at least two concrete fix directions** (here: fix the comparator's alignment vs
     fix the mux that introduces the offset) so the decision-maker chooses, not the
     Manager;
   - the **acceptance constraints as prohibitions** — e.g. "do NOT widen the three
     thresholds to make it pass", "prove it with the product's own probe function",
     "a truly different audio must still FAIL".
4. **Classify it `BLOCKED_DEPENDENCY` — LOCAL, not sprint-wide.** The rest of the wave
   keeps running on disjoint work; say so explicitly so the blocker is not read as a
   stop-the-round event.
5. **Do not** self-grant, do not edit the file, do not assign it to an owner whose
   allowlist excludes it. Wait for the grant.

### Why this is worth the extra file

An out-of-allowlist fix is the one class where the Manager's own "just proceed"
instinct is guaranteed wrong. Writing the request costs one artifact and keeps every
writer inside its granted scope — and because the micro-repro travels with it, the
eventual fix costs no full re-run. The request itself becomes the audit record of
*why* nothing was dispatched for that finding.
