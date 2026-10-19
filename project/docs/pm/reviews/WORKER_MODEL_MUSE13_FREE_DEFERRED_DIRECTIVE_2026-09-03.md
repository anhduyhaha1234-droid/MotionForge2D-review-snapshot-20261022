# Deferred worker-model directive — Muse Spark 1.3 Contributor Free

Recorded: 2026-09-03, approximately 20:21 +07.
Scope: user preference and route check only; not a sprint verdict or dispatch.

## User directive and activation boundary

- User requested exact model `ocgfree/muse-spark-1.3-contributor-free` for workers
  starting with the prompt issued AFTER the next independent Codex review.
- Use the existing custom 9Router endpoint. Keep `max` as the requested reasoning
  effort, but verify actual support; never claim effective max from configuration
  alone. Fallback remains OFF. Do not substitute a paid Contributor route,
  DeepSeek, a combo, or another spelling without user authorization.
- Do not change active workers, the currently issued S11 prompt, Manager or
  Git-only integrator assignments, or the global Hermes configuration now.
- At the future review boundary, corrections retain their exact task owner,
  session and branch. A model change alone does not authorize a fresh correction
  session. New tasks retain separate sessions, branches and worktrees per the
  approved dependency/parallelism contract.
- Preserve patch-only safety, task ownership, independent verification and all
  exit gates. This preference does not expand sprint scope or waive tests.

## Evidence from this check

Official source: [OpenCode Zen documentation](https://opencode.ai/docs/zen/)
(checked 2026-09-03). It lists the upstream model
`muse-spark-1.3-contributor-free` on the Responses endpoint as free for a limited
time. Its Contributor policy permits prompts and completions to be used to
train future Meta models. This does not prove any separate 9Router account cost.

The local `/v1/models` endpoint lists the exact requested `ocgfree/` route:

- tools: true; vision: false; reasoning: false;
- context window: 200000; maximum output: 64000.

These are local route declarations, not independently proven base-model limits.
In particular, vision and effective `max` reasoning are not verified.

An initial unauthenticated synthetic request returned HTTP 401 (missing auth).
An authenticated synthetic forced-tool request with requested
`reasoning_effort=max` returned HTTP 502 after 10.88 seconds. No successful tool
call or tool-result roundtrip was obtained. The check does not establish whether
this was transient upstream failure, adapter behavior or unsupported options.
There was no immediate retry or model fallback. No project code, private media,
secrets or historical worker context was included in the synthetic prompt.

Local diagnostic artifacts:

- `C:\Users\Admin\Documents\Codex\2026-08-29\less-b-t-bu-c-c\muse13-route-smoke.ps1`
- `C:\Users\Admin\Documents\Codex\2026-08-29\less-b-t-bu-c-c\muse13-route-smoke-result.json`

## Required handling at the next review

Status: `MODEL_PREFERENCE_RECORDED / USE_IN_NEXT_NEW_PROMPT`.

The user simplified the instruction after disclosure of the route-check and data
policy: use exact model `ocgfree/muse-spark-1.3-contributor-free` for workers in
the next newly issued prompt, as in prior model changes. Keep `max` requested and
fallback OFF. Do not change a session already running. No separate privacy,
benchmark, probe or activation gate is required before issuing that prompt.

All ordinary MotionForge2D ownership, exact-session correction, worktree,
parallelism, patch-safety, test and independent-review rules remain binding. The
502 probe above is retained as diagnostic history, not as a prompt blocker.

## Preserved state

- Canonical rules unchanged: SHA256
  `C9B068B2195461B1F867A5EC95714CEA3AB09881757F5607094574D15DDA428F`.
- Issued `S11_T02_T06_FULL_SPRINT_MANAGER_2026-09-03.md` unchanged: SHA256
  `57E9434AC7E8DF3A71C2437F9B100F72F024DDC8CC2566C95AF50F433B5E363E`.
- Hermes configuration unchanged. S11 integration status was inspected read-only
  and was clean; no sprint review or new exit verdict was performed this turn.
