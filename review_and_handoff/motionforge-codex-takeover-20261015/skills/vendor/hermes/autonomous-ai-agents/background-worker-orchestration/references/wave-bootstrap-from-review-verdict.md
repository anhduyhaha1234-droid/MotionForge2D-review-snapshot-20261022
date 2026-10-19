# Wave bootstrap from a review verdict — MF-RESKIN-V1 (verified 2026-09-17)

How a Manager session goes from "external review says CHANGES_REQUESTED, here is
your prompt" to two workers running on-scope, with the whole wave guarded —
without writing a single line of production code. First-try clean on
MF-RESKIN-V1; both lanes confirmed alive + on-scope ~3 min after dispatch.

## 1. Turn order that worked

```
read RULES (whole file, this turn)          -> RULES_LOADED  (path + SHA + sections)
read the review bundle's START_HERE/SCOPE   -> know the decision + what is authorised
read TEST: CRITICAL: the actual decision docs (REVIEW/PLAN/DIRECTION)
stat: wave base HEAD + porcelain            -> drift check BEFORE anything
stat: source media SHA                       -> match the locked fingerprint
probe: GPU / disk / engine presence          -> capacity facts for the packets
probe: model route on REAL response metadata -> not just the name in /v1/models
create: worktrees (native paths!) + EV tree
capture + verify: wave guard baseline
write: two worker packets                    -> one per Task ID
dispatch: both lanes in parallel             -> background + notify_on_complete
gate: artifacts exist, guard re-VERIFIED, no strays, workers ON-SCOPE
```

The guard baseline is captured BEFORE the worktrees are handed to a writer, and
re-verified immediately. Running the check twice in a fresh session is what
proves the check is real rather than post-hoc.

## 2. Evidence-root layout that reviewers could read

```
outputs/<wave>/<UTC-run-id>/
  manager/
    RULES_LOADED.md            path, SHA-256, size, lines, all 12 sections, discrepancies
    PREFLIGHT.md               repo table, source hashes, HW, route probe table, incidents
    SESSION_REGISTRY.md        Task | Session | Status | Model | write-set | runtime | EV | heartbeat
    packets/<TASK>.md          the full dispatch contract, one per Task ID
    logs/<TASK>.log            child stdout/stderr
    receipts/<TASK>.json       packet sha256 + bytes, cwd, model, argv shape, UTC, exit, duration
    guard/wave1/               baseline.json + baseline-verify.json + gate-recheck.json
    manager-tools/             launcher .py, guard .py, protected-targets.txt
  <TASK>/                      the worker's own evidence, written by the worker
```

`manager/` is the ONLY place the Manager writes. Task evidence dirs belong to the
workers.

## 3. Report the discrepancies you find (RULES §1)

The governance snapshot (`docs/pm/CODEX_PM_HANDOFF.md`) was **stale** — newest
entry `S11-C4-R4 — 2026-09-06`, containing no S12-LC3 / R7 / strategy-review
records, while the binding current state was the 17/09 review bundle. Held
correctly:
* it is a status snapshot, not rules, so it does not block dispatch;
* the **latest user directive wins** (the activated prompt), and that is what
  authorised the work;
* the Manager does **not** edit the handoff (canonical docs are outside the
  wave's write scope) — it reports the discrepancy in `RULES_LOADED.md` and
  proceeds.

Same shape for any stale governing doc: report, state which authority you used,
do not silently "fix" canon.

## 4. Packet anatomy that made two workers self-start correctly

Each packet carried, in this order: mandatory rules load (whole file + SHA +
`RULES_LOADED` ack, with the stop verb `BLOCKED_RULES`); role/authority (worker
implements only — never approves, never merges, never opens tasks); pinned
workspace table (worktree, branch, base SHA, runtime root, EV root) with
"drift ⇒ stop and report, no reset/checkout/clean/stash/restore"; the **exclusive
write allowlist** plus an explicit forbidden list; the binding model block; the
outcome; required evidence; a **machine-checkable acceptance table** (A1…A16-style
rows); required negatives that must FAIL loudly; and the terminal condition.

Two details that measurably helped:
* **Self-contained facts beat pointers.** The packet inlined the verified source
  SHA/size, the GPU VRAM, free disk, and "ComfyUI not found in these 4 paths —
  do NOT conclude the machine has none elsewhere". Both workers preflighted the
  same facts and immediately began real work (one found the demo-30 s source on
  its own; the other checked HEAD/disk/GPU then started engine discovery).
* **Write "unknown ⇒ unsupported / unmeasured, never success"** explicitly, and
  state that fake-transport tests are adapter tests only whereas real inference is
  the model proof. This is the anti-fabrication clause; put it in the packet, not
  just in the report request.

## 5. Wave gating (do not fill slots)

| Wave | Tasks | Gate |
|---|---|---|
| 1 | GOLDEN + COMFY (parallel) | before-anything: disjoint write-sets, disjoint runtimes, disjoint EV; GPU serialised by an exclusive lease |
| 2 | PROPAGATE | only after GOLDEN's fixture is FROZEN |
| 3 | BENCH | only after all upstream artifacts are frozen |

Opened wave 1 only. Recorded in `SESSION_REGISTRY.md` **why** PROPAGATE/BENCH were
not opened ("depends on a freeze that does not exist yet") so the reviewer sees a
deliberate slot decision rather than an omission.

## 6. Incident record (both self-inflicted, both resolved, both reported)

1. **MSYS worktree path bug.** `git worktree add /c/Users/… -b …` made git record
   `C:/c/Users/…`; a stale `C:\c` junction pointing at `C:\` existed, so the
   worktrees were rooted at the drive root. Detected via
   `git worktree list | grep <marker>`. Fixed by `git worktree remove <recorded
   path> --force`, `git branch -D`, then recreating with native `C:/Users/…`,
   then removing the junction. **Post-incident verification by counts** confirmed
   no damage: Hermes home (config bytes, 146 skills, 305 session files,
   `projects.db` size, `SOUL.md` bytes), `git rev-parse HEAD` and
   `git ls-files | wc -l` for MAIN (546) and the wave base (1,837).
2. **`hermes sessions export <id>` dumped 444 MB** into the working directory. It
   was deleted immediately and never counted as an artifact. Read sessions with
   read-only SQL instead.

Both went into `PREFLIGHT.md` under an explicit "Incidents during preflight
(reported, resolved)" heading. Reporting your own self-inflicted, already-fixed
incident with the verification that proves no damage is what keeps the packet
reviewable; omitting it would have looked like the worktrees appeared by magic.

## 7. ETA table shape the user accepted

Columns: milestone | content | ETA anchored to the live `+07` clock. Rows:
heartbeat #1, G0 baseline, engine adapter, wave 2, G1 visual proof. Plus a
"what could slip" line naming the concrete risk (model downloads, engine
discovery from zero) and the promise to report immediately on slip. Concrete ETA
ranges come from measured facts (disk, VRAM, "setup from zero"), never from
optimism.
