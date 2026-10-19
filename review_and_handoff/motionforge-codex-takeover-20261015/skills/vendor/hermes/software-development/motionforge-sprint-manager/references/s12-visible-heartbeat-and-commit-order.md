# S12 visible-heartbeat + commit-order (2026-09-07)

Session-specific detail for the "Visible heartbeat" and "commit order" bullets
in SKILL.md. Facts from the live S12 run — shapes to recognize, not doctrine.

## Heartbeat visibility gap as observed

- `hermes cron list` shows per job: Name / Schedule / Repeat / Next run /
  Deliver / Script / Mode / Last run. The S12 job as created defaulted to
  `Deliver: local` with the note "its output is saved but will NOT be
  delivered back into this session". Fix: `cronjob(action='update',
  job_id=<id>, deliver='origin')` — verified same turn (next_run_at moved to
  next 10-min slot, Deliver flipped to origin).
- Same turn: PAUSE the prior sprint's reminder cron (S11 15m job paused while
  S12 10m created) so one Manager session never gets double-nudged.
- Gateway-off warning verbatim in cron list output: "Gateway is not running
  — jobs won't fire automatically." While that warning is present, cron is
  decorative: keep the bg-loop fallback AND show per-status-turn proof
  (cron list + remind-log tail + worker fresh message/WT state).
- Remind script shape (copy per sprint, rename SID/LOG): `remind_s12_muse.py`
  under `%LocalAppData%/hermes/scripts/` — runs `hermes chat -q "tiếp tục
  làm việc đi" -r <manager-sid> -m cmc/meta/muse-spark-1.3-contributor
  --provider muse -Q`, appends to `logs/remind_s12.log`, silent exit 0 on
  success, prints REMIND_FAIL only otherwise. Runs as no-agent cron
  (`*/10 * * * *`, script=remind_s12_muse.py) so stdout IS the delivery.
- User's trigger phrase: "heartbeat đâu sao ko thấy" (also earlier: 10-min
  cadence demanded 2026-08-31 because 30' "thấy hay dừng lắm"). Any complaint
  about not SEEING progress ⇒ treat as heartbeat defect first, not worker
  defect: check deliver mode + gateway state + log tails before touching
  workers.

## T05 commit-order shape as observed

- Worker state that triggers it: all gates green (pytest 15 / TSC 0 errors /
  Playwright 15 passed + 1 skip) + worker writes "Chưa commit — chờ lệnh"
  (303 msgs / 154 tools). File set: 11 files, 100% `frontend/` allowlist,
  0 backend, WT porcelain shows only the allowlist.
- Commit-order nudge (via `--resume` on the EXACT owner, background +
  notify_on_complete): order `git add` of the allowlist ONLY + commit with
  the lane message + NO push + TASK_SUBMITTED with SHA + file list, and
  explicitly "Không chạy thêm gate nào nữa" to stop gate-looping.
- Manager verify right after (zero model calls): `git show --stat <sha>`
  (file list + counts), allowlist check
  (`git diff <base>..<sha> --name-only | grep -cv '^frontend/'` must be 0),
  `git diff --check` exit 0, backend regression pytest on the related scope
  (T03C suite, since T05 touched no backend).
