# S11-C4-R4 in-flight retry + zero-model-call poll (2026-09-06)

Source: R4 resume of exact owner `20260905_192221_6da09b` in Manager
`20260905_162953_5a5cda`. Worker committed `7c58c37` (3 files test-only,
diff-check clean) + focused C4R1 6 passed / 5.86s, then hit transient error.

## 1. Transient `CommandCode server_error` is retryable, not terminal
- Transcript (msg 181695, 2026-09-06 21:22:24 +07): `[CommandCode error:
  {"type":"server_error","message":"Failed after 3 attempts. Last error:
  Service temporarily unavailable. Please try again shortly."}]`
- Treat exactly like 502/504 per rules §7: `RUNNING_RETRY_WAIT`, wait 5 min,
  resume SAME owner + SAME model/route, unlimited cycles. Never create a
  replacement worker, never swap model.
- Before judging the lane failed: check tip movement + porcelain +
  `show --stat`. Here the substantive work had already landed (`7c58c37`
  on `codex/s11/c4-r2`), so the error belongs to a post-verify trailer,
  not the correction itself.

## 2. Zero-model-call liveness poll via state.db (read-only)
- Open `%LocalAppData%/hermes/state.db` only via
  `mode=ro&immutable=1`; never copy/vacuum/mutate.
- Track per-session progress by global `messages.id`, not by the session
  row's `message_count`: after R4 resume the row still read 182/84 while
  `select count(*)` already returned 344 (global ids vs per-session
  counter). Recipe:
  `select max(id) from messages where session_id=<owner>` → remember it →
  later `select id,role,tool_name,datetime(timestamp,'unixepoch','+07:00'),
  substr(content,1,200) from messages where id><last_seen> order by id`.
- `NEWER-ROWS: 0` after 8 min with no tip/porcelain advance = audit now
  (process scan, log tail, session input state); tip advanced = working,
  keep waiting.

## 3. Single immutable evidence root per round
- Mid-preflight a second root `20260906-211400-R4-final` was created
  alongside `20260906-210700-R4-final`; removed immediately, single root
  kept. Never let two `R4-final` roots coexist; never reconstruct old
  commands as if they ran in R4 — `commands.jsonl` rows carry real
  start/end ISO UTC + reviewed HEAD + exit.

## 4. Guard tool path + arg shape
- `write_set_guard.py` lives under MAIN
  `C:/Users/Admin/MotionForge2D/docs/pm/tools/`, NOT inside the task
  worktree (bare `docs/pm/tools/...` from the worktree = exit 2
  `No such file or directory`). Call via absolute MAIN path.
- `capture` REQUIRES `--root <worktree> --manifest <path>`; bare
  `--path` alone exits 2. Capture 10 entries + verified snapshots BEFORE
  resume; baseline must show the pre-patch test image (`95eb2e5d`
  20741B 554L), not an already-patched file.
- Line-count note: guard `_line_count` reported 44 vs naive
  `bytes.count(b'\n')+1` = 43 on `guard_baseline.json` (trailing-newline
  handling). Guard's count is authority; record both when they differ.
