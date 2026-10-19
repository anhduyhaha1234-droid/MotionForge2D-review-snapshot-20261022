# Watchdog terminal-marker design (S11-C1 lessons, 2026-09-04)

No-agent watchdog (cron `--no-agent` script, SILENT unless action) supervising
resume-exact-session worker lanes. Three false-BLOCKED bugs found live — all
fixed and proven SILENT after fix.

## 1. Terminal marker is ground truth, not log silence

A lane with frozen dispatch.log + quiet session is DONE, not stalled, if the
worker already wrote its terminal line. Check terminal FIRST, stall signals
second. Original bug: watchdog had no terminal check, so two SUBMITTED lanes
were nudged then declared `STALLED_AFTER_NUDGES (BLOCKED?)` on loop for ~2h.

## 2. Matcher rules (all three learned from live false positives/negatives)

- Tolerate markdown prefixes before the marker: `**`, `-`, `+`, `#`, `>`,
  whitespace. Real terminal was `**TASK_SUBMITTED — ... EXIT.**` — a strict
  `^TASK_SUBMITTED` regex missed it (false NEGATIVE → false stall).
- SUBMITTED counts only with an `EXIT=` trailer present (wrapper finished)
  — not a mid-log quote or REPORT citation. Match ANY `*_EXIT=` suffix
  (`EXIT=`, `NUDGE_EXIT=`, `NUDGE2_EXIT=`, `FOLLOWON3_EXIT=`, `FINAL_EXIT=`,
  `LADDER_EXIT=`, ...): wrapper suffixes vary per dispatch, so never
  whitelist specific prefixes — a bare `EXIT` alternative in the regex
  covers all current and future variants.
- `NEEDS_T04B_PRODUCT_FIX` counts only as a line-leading marker. A REPORT
  diff citing the string in prose ("KHÔNG cần T04B (`NEEDS_T04B...`)")
  caused a false POSITIVE that nearly opened a conditional lane for nothing.
- Read the WHOLE dispatch.log, not the last N bytes — the trailer can sit
  outside any tail window (file was ~40KB; full read is cheap).

## 3. Watchdog's own lines must count as evidence

If the watchdog writes signal lines (e.g. `WATCHDOG-SIGNAL tip=<sha>
TASK_SUBMITTED ...`) into the lane log, the matcher must accept them when
the cited tip matches HEAD — otherwise self-written evidence confuses the
matcher and the lane wedges.

## 4. Clear stale nudge state on design change

`nudges[tip]=2` (max reached) persists in state JSON across script edits.
After fixing the matcher, delete stale nudge counters or fixed lanes stay
stuck in `STALLED_AFTER_NUDGES` forever.

## 5. Watch the Manager too

Worker-watch without manager-watch caused the 2h idle gap: all lanes DONE,
watchdog correctly SILENT, but nobody reminded the Manager to run verify +
merge next. Rule: when all lanes terminal-DONE and manager gates/exit items
are still open after >60m, the watchdog pings the MANAGER session.

## 6. Gateway-off reality (Windows)

Cron never fires and output never delivers when the gateway is off. Keep an
independent `sleep`-loop process as backup; kill the loop once the gateway
is on to avoid double-nudges. Cap at 2 nudges per tip, resume the EXACT
owner session only (never a new worker), never write git state.

## 7. Route pinning + instant notify

- Nudge resumes must pin the model explicitly
  (`-m <model> --provider <provider>`); never rely on config defaults.
- Verify route per session via `session_model_usage`
  (model / billing_provider / last_seen). `task='approval'` rows are system
  calls, not worker calls — don't misread them as route violations.
  Historical rows from prior sprint phases are not current violations:
  compare `last_seen` against the current dispatch window.
- Worker EXIT → report the user IN THE SAME TURN, before any further
  verify work. Silence-until-asked is the failure mode that started this.

## 8. See also

- `references/cross-lane-gate-seed-interaction-triage.md` — what happens AFTER
  the watchdog goes SILENT with all lanes DONE: zero-conflict integration
  merge with a RED combined gate is usually a gate-contract × stale-seed
  interaction (not a defect in either lane). Isolate the RED item, trace both
  sides, route the seed owner with an exemplar commit, re-run the full gate.
