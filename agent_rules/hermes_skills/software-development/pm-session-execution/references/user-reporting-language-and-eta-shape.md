# Reporting to the user: language, shape, ETA

Applies to every progress/verification report a Manager sends to this user during long
autonomous orchestration (worker waves, sprint gates, proof runs).

## 1. Language — Vietnamese

- **Write the report in Vietnamese.** This user corrected the agent **twice in one session**
  ("tra loi bang ting viet di", then an out-of-band "trả lơi f bằng tiếng việt cơ mà") after
  receiving a report whose headings and prose were English. Treat an English-heavy report as a
  violation of the preference, not a stylistic choice.
- Keep **machine tokens verbatim** in their original form because they are identifiers the user
  greps for: `RULES_LOADED`, `PREFLIGHT_OK`, `RUNNING`, `TASK_SUBMITTED`,
  `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`, `CHANGES_REQUESTED`, commit SHAs,
  branch names, file paths, command lines (`ruff check --select F`), metric names, verdicts
  (`TECHNICAL_FAIL`, `NOT_REVIEWED`).
- Everything else — headings, table captions, explanations, risk notes — in Vietnamese.

## 2. Shape, in this order

1. **Status line first** — done / running / blocked, one line, no preamble.
2. **A table of numbers you actually measured**: file counts, byte sizes, line counts,
   SHA-256 prefixes, port numbers, durations, VRAM/RAM, tool-call counts. Numbers, not adjectives.
3. **What is still open / at risk**, itemised, with the concrete blocker for each.
4. **ETA table anchored to a real date with the local offset** (+07 for this user), one row per
   milestone, each with the measured basis (tools per minute actually observed, artifacts on
   disk, bytes already downloaded). Add the reason for any slip and for any milestone that
   cannot be estimated yet.
5. **Next action you are taking** (what you dispatch / verify next), so the message is not a
   dead end.

## 3. Provenance and honesty rules

- Separate **"I re-ran this myself"** numbers from **the worker's self-report**. Say which is which.
- Never restate a worker claim as a fact. Never claim a visual/quality verdict when the route has
  no vision — mark it `NOT_REVIEWED` and name who must look (the user or the reviewer).
- Report a slip or an incident **in the same message where the rest looks green**; never wait for
  the next heartbeat, never quietly re-estimate, never bury it under a success table.
- Keep failures and self-disclosed defects as first-class rows (`disposition: fail` + note). Do
  not smooth them into a green summary.
- Do not use test counts as a substitute for the actual deliverable (a clip/artifact/hash).
- End the packet in chat, addressed to the user; never auto-send review/`APPROVED`/`CLOSED`.

## 4. Answering "how long until everything is done?"

The user asks this in shorthand ("bao h xong het"). Answer with:

- the status of each task (done / running / queued) — not a single unanchored number;
- an ETA **per milestone** anchored to a date and the +07 timezone;
- the measured basis for each estimate (observed tools/minute, artifacts already on disk,
  bytes already fetched);
- the top 2–3 things that could push the ETA out, named up front, before they happen.

## 5. Dispatch safety (mutating tools)

Before invoking a script that stops/starts/deletes/overwrites state (server-stop tools, cleanup,
snapshot writers), **read its source first**. A script with no `argparse` ignores unrecognised
arguments and executes on invocation, so probing it with `--help` performs the action — one round
overwrote the previous round's shutdown evidence exactly this way. Require the worker to record
it as a `fail` row in its gate matrix rather than hiding it, and carry the warning into the
handoff document of the next task.
