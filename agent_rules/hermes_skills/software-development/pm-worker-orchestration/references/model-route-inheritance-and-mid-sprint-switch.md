# Model-route inheritance & mid-sprint model switch (worker dispatch)

## Inherit, don't pin

Dispatch workers as `hermes chat --resume <session> -q "..." -Q` with NO
`-m` / `--provider` pin, so each worker inherits the Manager session's
active model. An explicit `-m <model>` pin overrides the user's current
model and goes stale the moment the user switches models mid-sprint
(workers keep burning the old route, including quota-dead free tiers).

## Mid-sprint switch procedure (user: "move all workers to my model")

1. `process(action='list')` + `ps` — inventory running workers and their
   cmdlines; confirm none carry `-m <old-model>`.
2. New dispatches inherit automatically (no pin). In-flight workers on the
   old route: let short ones finish, re-dispatch long ones only if the
   route is actually failing (e.g. HTTP 502 FreeUsageLimitError).
3. Grep scripts, prompts, and evidence dirs for stale references to the old
   model (e.g. `NUDGE_MODEL` in watchdog scripts) and disable them —
   comment out, don't delete, with date + reason.
4. Prove zero: `ps` shows no old-model cmdlines; recursive grep over live
   scripts/evidence shows no active references (DB copies and history logs
   don't count).

## Quota errors are provider errors, not task failures

HTTP 502 / FreeUsageLimitError on a free-tier route means "switch route",
not "task failed". Retry on the new route; never re-pin the dead one.

## Wrapper-exit-before-commit two-step nudge

CLI wrapper processes often EXIT before the worker finishes gate+commit.
Split follow-ups: step 1 = run gate + stage evidence; step 2 (separate
nudge, re-testing FORBIDDEN) = commit only.

## Misrouted-owner incident honesty

If a commit lands from the wrong owner session: record it honestly in
LOG/REPORT (which session, what it made), have the real owner re-derive
independently with keep/drop bytes documented, never rewrite history.

## Resume-may-fork: verify the session id after every --resume dispatch

`hermes --resume <owner>` against a terminal (`agent_close`) session can
mint a NEW session carrying the correction prompt instead of continuing the
owner (observed twice in one lane: R1→R2 and R2→R3 each produced a fresh id).
After every resume dispatch, query state.db for the newest session, its
model, and its first user message, and confirm whether the owner continued
or a fork was minted. Record the true lineage in the registry (R1 owner →
fork id); never claim "resumed exact owner" from the command string alone.
Single-active-writer still holds while the old session is terminal, but the
registry must name the fork or later audits will misattribute the work.

## Vision prose is not file truth

Vision-analysis wording can leak into correction packets as if it were file
content (a scene description saying "standing" nearly triggered a file fix;
grep over all evidence plus the four new files returned zero hits outside a
test that bans the word). Before dispatching any correction that quotes file
content, grep the actual files and evidence dirs for the quoted string. Zero
hits means no correction round — record the false positive in the registry
instead of burning a worker round proving nothing changed.

## Exact-id pin when alias confusion is proven

Inherit-don't-pin stays the default, but when an alias/transposition
incident is proven (two near-identical model ids both pong yet route
differently — T00's transposed tokens), pin the exact model id in the
dispatch string AND append a model errata file preserving the original
registry text. On the next user-ordered switch, grep prompts, registry, and
live cmdlines for the old id and update every live reference; history logs
and DB copies don't count. In-flight workers on the old route run to their
verdict — only NEW dispatches and resumes use the new id — and a lane-scoped
switch never touches S12/Lunar/global routing.

## Garbled user-typed model ids

Users type model ids by hand and garble them (observed: `cmc/.muse -spark-1.3-contribvutor` for `cmc/meta/muse-spark-1.3-contributor`). Never paste the garbled string into a dispatch: normalize to the closest known exact id first (match provider prefix + model family against config.yaml `providers.*.model` and recently probed ids), then PROBE the normalized id (`hermes -z "ping" -m <id> --yolo` → pong EXIT 0) before any worker dispatch. Record the switch in the registry as `USER MODEL OVERRIDE <lane>-v<n>` with from→to ids, who ordered it, and probe evidence; update the live continuation prompt file to the new id; retire the old id for the lane (grep prompts/registry/live cmdlines; history logs and DB copies don't count).
