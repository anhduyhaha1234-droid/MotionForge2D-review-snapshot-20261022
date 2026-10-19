# Two-manager waves, upstream-flap recovery, freeze→produce→review (S12-R7, 2026-09-16)

Playbook distilled from a 5-lane wave split across two Manager chats on one shared
wave-base commit (Manager B = orchestrator; Manager A = separate chat, separate lanes).
Every pattern below was exercised end-to-end in the same day.

## Two-manager split
- Record the split in YOUR registry the moment it exists: which owner sessions belong to
  the other manager ("coordination transfer only — writers unchanged"), so you never
  resume/dispatch them. Confirm the other manager's workers via process table (PID +
  session id parsed from `chat -q` command lines), not by assuming.
- The other manager's verified output arrives as a machine-readable handoff JSON
  (`EXPORT_HANDOFF.json`): lane commits + exact SHAs + diffstats + per-lane guard results +
  no-active-writer evidence + answer map + limits/non-claims + terminal status. Consume it
  read-only; copy the producing manager's session id into your registry from `produced_by`.
- Sole integrator: exactly ONE manager owns transport; the other manager never merges.
- Every lane syncs to the SAME wave-base commit before correction (`git merge --ff-only`),
  so transport merges are zero-conflict when write-sets are disjoint — PROVE disjointness
  from the handoff (empty intersection of path lists) before dispatching transport.

## Upstream-flap (502) recovery loop — ran 2 cycles in one day, zero bytes lost
Symptom: worker turn dies mid-work with
`API call failed after 3 retries: HTTP 503: [...][502]: fetch connect timeout`.
1. BYTE-SAFETY AUDIT immediately: `git status --short` in each dead lane's worktree.
   Workers edit early / commit late — uncommitted edits are normal and must be intact.
   The surviving file list (M/??) becomes the resume-state list you quote in the nudge.
2. Health probes: local gateway `/models` HTTP 200 does NOT mean inference works — the
   completions upstream is a separate hop. Probe with a real tiny inference
   (`hermes chat -q "Reply exactly: PROBE_OK" ...` under an external timeout).
   `/models` 200 + probe timeout = still flapping → wait another cycle.
3. Cycle: wait ≥5 min from death → probe → on success resume the SAME session (same route,
   same model, fallback OFF) with a continuation nudge. Unlimited cycles; transient
   errors are never a terminal state.
4. Continuation nudge shape (worked verbatim in Vietnamese; keep the five elements in any
   language): (a) blame the gateway, NOT the worker ("lượt trước bị ngắt bởi lỗi kết nối
   gateway tạm thời — KHÔNG phải lỗi của bạn"); (b) restate invariants (route/model/scope/
   allowlist unchanged); (c) list on-disk state (modified + new files, uncommitted);
   (d) "verify state then continue from the stop point — do not redo completed work";
   (e) "do not ask questions."
5. Resume mechanics: append console output with `>>` and append `RESUME<N>_EXIT=$?` after
   each wave; `grep -c RESUME` on the console tells you how many waves the lane survived.
   Prefix resume commands with `sleep 30` so the ≥5-min mark is guaranteed even when the
   dispatch happens right at the boundary.
6. When several lanes die at once, they are independent resumes — dispatch all three in one
   batch after one probe; don't serialize per-lane waits.

## Stale background notices
BG completion notices can be delivered very late and OUT OF ORDER (a heartbeat-cycle notice
arrived hours after its run; two lane notices arrived after their work was already
processed). Never act on a notice alone — reconcile against real state first: console
`stat` size/mtime + `tail -c N | tr '\r' ' '`, live proc list
(`Get-CimInstance Win32_Process` filtered `chat -q`), lane `git log`/status. Disk is truth;
the notice is only a hint.

## Freeze → produce → independent review (contract-first lanes)
1. Owner drafts `CONTRACT.md` grounded in real code (file:line refs, exact schema block,
   per-phase fail-closed code tables, numbered open questions).
2. Manager writes a separate rulings doc: one explicit ruling per open question
   (adopt / revise + rationale), pinned to the acceptance rows it serves.
3. QA co-signs each ruling CONFIRMED/REVISE **with real evidence numbers** — here the QA
   REVISE overturned both the reviewer's assumption and the contract draft by quoting
   actual persisted values. Always demand values; never accept "looks fine".
4. Amendments get versioned sections appended to the ruling doc (v0.2, v0.2.1); the
   production prompt cites every freeze artifact by absolute path.
5. Production may HARDEN a ruling when real data contradicts it (e.g. clip-to-frame
   instead of deny for padded boxes). Acceptable when bounded + deterministic + documented
   + surfaced as an explicit flag — Manager then reads the actual code before accepting and
   records the amendment. Never let a hardening pass silently.
6. After production, QA runs an INDEPENDENT coverage check; gaps it finds (missing negative
   fixtures for amended behavior) go back to the same owner as a small bounded follow-up
   turn — not a new session, not a new write-set.

## Manager verification sequence (per worker submission)
1. Scope: `git show --stat` every commit; every path ⊆ lane allowlist; tree clean; count
   commits; record tip SHA.
2. Independent re-run: worker green is a claim, not evidence. Re-run the decisive suite in
   a BG process (`-p no:cacheprovider`, isolated short `--basetemp`, raw output → evidence
   dir); compare counts against the worker's numbers.
3. Guards: `write_set_guard.py verify` allow-manifest (with `--allow-change` per permitted
   path) + protected-manifest (no allow-change). Both must be `VERIFIED`, failures 0.
4. Read the full report, then open the CODE for every flagged deviation (hardening, legacy
   alias, compatibility shim) and judge it — flags are to be verified, not believed.
5. Out-of-gate reds: classify each as (a) pre-existing (prove via base revision), (b)
   contract-mandated (old expectation superseded by the frozen spec), or (c) regression.
   For (b): file `FINDING_*.md` — fact + exact node ids + why superseded + exact minimal
   proposal + proposed bounded owner. Never edit outside a write-set: "scope needing
   another file gets an exact minimal proposal, not a silent edit."

## INT transport round (single ordered round)
- One round: ordered merges by dependency preference (A-lanes → B-lanes → QA), each
  `--no-ff` with a recorded merge message; per-lane pre-check (owner terminal + allowlist)
  immediately before that lane's merge.
- Conflict → ABORT instantly, report BLOCKED with the exact file/object; hand back to the
  exact owner. Never hand-fix conflicts.
- After all merges: static gates (compileall, py_compile changed files, `ruff check
  --select F`), `git diff --check`, delta-path count vs base, ledger + RAW_PROVENANCE into
  the wave evidence root. No push.

## Wave bookkeeping that paid off
- Heartbeat per wave: small PS1 that timestamps, prints each lane console size/mtime, and
  counts live `chat -q` procs; armed as a `sleep 1140` BG loop with notify-on-complete.
  Silent when OK; report only on change/blocker.
- Incident doc gets a new "WAVE n" section per recurrence instead of a new file; the
  registry row for every lane is updated on every transition with its proc id.
- Registry rows carry: session id, status, worktree/branch, exclusive write-set. Finding
  docs are separate files referenced from the packet.

## Shell/tooling pits worth remembering
- Commands with nested `$(...)` substitutions inside double quotes can trip a parser
  hardline block ("malformed executable payload ... cannot be executed"). Split into
  separate simple commands, or write a small script file, instead of retrying the same
  shape. (Happened twice; both times restructuring fixed it immediately.)
- Lane consoles are append-only across all waves: one file per lane, `RESUME<N>_EXIT`
  markers, and `tail -c N | tr '\r' ' '` reads the last screen cleanly from bash.
- Worker worktrees may need `git -c safe.directory='*'` on every invocation (dubious
  ownership), and `git -C /c/abs` can fail spuriously on this host — `cd` first, use
  relative paths.
