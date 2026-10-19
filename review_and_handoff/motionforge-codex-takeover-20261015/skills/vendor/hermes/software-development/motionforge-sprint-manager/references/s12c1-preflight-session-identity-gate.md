# S12-C1 preflight: session-identity gate, contract locate, reminder reconcile (2026-09-08)

Session `20260908_011327_cc3b74` received the S12-C1 packet (13 finding groups
R01–R13, CHANGES_REQUESTED/NOT_APPROVED/NOT_CLOSED, 32-row locked matrix) but was
NOT the packet's required Manager `20260905_162953_5a5cda` (still ALIVE, 412 msgs).
Did read-only preflight + fresh evidence root only; dispatched nothing. Lessons:

## 1. Session-identity gate is step zero (same rank as RULES_LOADED)

- Compare current session ID (`HERMES_SESSION_ID` env) against the packet's exact
  required Manager ID, and check whether that Manager is still ALIVE
  (`hermes sessions list` + recent activity), BEFORE building evidence/MATRIX/guards.
- Mismatch + required Manager alive ⇒ `BLOCKED_OWNER_SESSION`: read-only preflight
  only. NO dispatch, NO Git writes, NO worker nudges, NO INT01 creation from the
  wrong session — a rival integrator repeats the R13 role violation (§8.1).
- Record the blocker + handoff (resume the exact Manager, which must re-verify
  registry + read-only Hermes state itself) instead of doing the work anyway.

## 2. Locate every cited contract path before claiming it missing

- Packet cited `TARGET_PROFILE_2D_SOURCE_LOCKED.md` at the worktree root; it lived
  at `docs/pm/`. `find` every cited path first — a missing-path claim without a
  search is a false blocker. Same for `MASTER_PLAN_V1.md` WS-08/WS-09/G5/F/G
  (verified via grep: WS-08 line ~1006, G5/F/G lines ~1218+).

## 3. Snapshots go stale — re-run porcelain on every tree acted on

- MAIN dirty count moved 25 → 89 within one turn. Canonical `e1474af…fd44`
  local==remote verified 3×; all 9 task worktrees + S11 `1f5936d…` porcelain 0.
  Never dispatch off the session-start snapshot.
- MSYS quirk (re-confirmed): `git -C /c/abs/path` falsely errors "cannot change
  to" though the dir exists — `cd <dir> && git …` instead.

## 4. Reminder-loop reconcile = identify, then record (never blind-kill)

- `wmic process` cmdlines (desktop 25020 / serve 36868 / ocg_free.py 13336 /
  http.server 7480 — none the reminder) + `hermes cron list` (none) + schtask
  query (no S12 task) + script/log mtimes (remind log last 01:14 +07, heartbeat
  beats 1–15 to 18:13 GMT) ⇒ loop already stopped. Killed nothing, touched no
  global configs, per packet (only the owned loop, never generic python/Hermes).
- Ports 3187/8187/18769 free (netstat empty) — no demo/pilot touched.

## 5. R13 shape to recognize

- INT01 LOG line 3 self-declared "Manager acts as Git-only owner; no worker
  dispatch" — contradicts §8.1 (exactly one DEDICATED integration owner).
  Transfer the Git role out after zero-competing-owner proof
  (`integration_candidates: []`, no INT01 id in session list); session length
  alone never justifies replacing worker owners. Duplicates stayed contained
  (T01 `…481996` FROZEN_ACK, T06A `…0c1e8a` STOPPED); T01 cwd metadata
  (`C:\Users\Admin`) distrusted vs commit payloads proving the task worktree.
- Pre-existing staleness noted, not rewritten: INT01 REPORT §6 recorded
  `684ea9f…` pushed but live HEAD is `e1474af…` (docs-only amend with one
  force-with-lease) — C1 packet needs explicit errata, old submission stays
  historical (append-only ERRATA.md pattern).

## 6. Explicit user-authorized session switch lifts the identity block (2026-09-08 follow-up)

- User order (verbatim VN): "M cu lam di t doi season cho do njawng context"
  (= keep working; I switched session to lighten context). That is EXPLICIT
  owner-transfer authorization, not a rival integrator: BLOCKED_OWNER_SESSION
  lifts for the explicitly authorized new session. Record the verbatim order +
  old Manager ID -> new session ID in ERRATA.md + SESSION_REGISTRY.md the same
  turn the switch is invoked.
- Authorization changes WHO may act, never the rigor: the new session must still
  re-verify registry + read-only Hermes state itself (zero competing INT01
  proof, fresh porcelain on every tree acted on, re-captured byte guards)
  before any Git write or worker dispatch.
- Distinguish from ambiguous chatter, which never authorizes anything:
  "m ko nhac nua a?" = question, NOT a stop; "alo" / "dang chay chua?" =
  status check, NOT a stop; "tu tu" / "dung" / "doi ti" = explicit HALT.
  Only an explicit "lam di / chay tiep di" tied to a session-switch reason
  counts as transfer authorization.

Note (verified 2026-09-08): SKILL.md already references this file in the
Manager skill's evidence-layout reference chain — no further pointer patch needed.
Section 6 above also records the follow-up: an explicit user-authorized session
switch ("doi session cho do nang context") LIFTS the identity block for the
named new session; see `references/s12c1-w4-t03c-unmocked-repro-and-session-switch.md`
for the re-anchor checklist the new session must run first.
