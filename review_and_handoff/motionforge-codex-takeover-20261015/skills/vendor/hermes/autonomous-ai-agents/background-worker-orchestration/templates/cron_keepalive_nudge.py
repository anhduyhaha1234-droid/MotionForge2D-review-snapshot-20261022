# Keep-alive nudge for a stalled Hermes manager/worker session.
# Cron no_agent job (e.g. schedule "*/30 * * * *"), Windows-safe.
# Known-good recipe — verified 2026-09-04 (session 20260903_200004_c25766, S11-2-muse), refined same day.
#
# Rules that make this work:
#   - .py NOT .sh: the cron scheduler hands Windows backslash paths to bash,
#     which strips them (exit 127 "C:UsersAdmin...: No such file"). Python
#     handles Windows paths natively.
#   - ALWAYS pin -m/--provider on the resume: `hermes chat --resume <sid>`
#     without them uses the PROFILE DEFAULT model, not the session's stored
#     model_config (verified: banned route ran). model_config column stays
#     untouched, so the wrong-model turn is invisible in the session record.
#   - Stream hermes chat output to the LOG FILE handle (stdout=logf), NEVER
#     capture_output=True. Capture swallows the nudged session's response,
#     leaving only start/exit/end lines in the log — you lose the evidence
#     of what the manager actually did ("did it continue?"). Verified: a
#     capture-based version logged 3 lines per run for an hour while the
#     manager kept answering; switching to stdout=logf restored full replies.
#   - f.flush() after writing the "start" marker BEFORE the subprocess runs:
#     Python buffers f.write() calls, so without flush the subprocess's
#     direct-fd writes can land in the file BEFORE your start line (observed
#     interleaving). Order: write start -> flush -> run -> write exit -> flush.
#   - Silent stdout on success (empty stdout = no cron delivery); print ONLY
#     on failure + exit non-zero so `cronjob list` last_status flips to error.
#   - Retry once after ~20s on exit 1/2 (Hermes CLI retryable codes).
#   - Observer is the log file + cron last_status (desktop chats have no
#     live cron delivery channel). Test with `cronjob action=run` and read
#     execution_success/execution_error before trusting the job.
#   - If the managed session STILL stalls between nudges, tighten the cron
#     schedule (30m -> 15m -> 10m). User pattern: "30p nó vẫn bị dừng" (2026-09-04).
#   - Do NOT convert this job to agent-mode (no_agent=false): the cronjob
#     tool exposes NO model/provider params, so an agent-based job runs the
#     profile DEFAULT model (banned-route risk) and delivery is skipped
#     anyway. Keep it no_agent + this script.
#   - Job stuck "already running" (agent.log: "Job '…' already running —
#     skipping" at every boundary + stale last_run_at): pause then resume the
#     cron job to reset the running flag, then cronjob action=run once.
#     Verified 2026-09-05.
#   - When the user points the reminder at a NEW session id: read
#     sessions.model/models.model_config from state.db FIRST, patch SID +
#     MODEL + PROVIDER + LOG (fresh log per session), rename job, then
#     cronjob action=run once and confirm a start block in the new log.
#     If the managed session answers BLOCKED_MODEL_ROUTE (its prompt rules
#     demand an exact model id absent from the router catalog; zero
#     dispatch), the user must fix the route — report it, don't patch rules.
#     Verified 2026-09-05.
#
# Verify the model actually used after a run:
#   grep -a "<SID>" "$LOCALAPPDATA/hermes/logs/agent.log" | grep -a "Turn ended"
#   -> the `model=` field names the real model per turn.

import datetime
import subprocess
import sys
import time

HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
SID = "<SESSION_ID>"
MODEL = "<MODEL, e.g. ocgfree/muse-spark-1.3-contributor-free>"
PROVIDER = "<PROVIDER, e.g. custom>"
MSG = "<nudge text, e.g. tiếp tục làm việc đi>"
LOG = r"C:\Users\Admin\AppData\Local\hermes\logs\<name>.log"


def run(logf):
    cmd = [HERMES, "chat", "-q", MSG, "-r", SID, "-m", MODEL, "--provider", PROVIDER, "-Q"]
    return subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode


with open(LOG, "a", encoding="utf-8", errors="replace") as f:
    f.write(f"=== {datetime.datetime.now():%F %T} start ===\n")
    f.flush()
    rc = run(f)
    f.write(f"exit={rc}\n")
    f.flush()
    if rc in (1, 2):
        f.write("--- retry after 20s ---\n")
        time.sleep(20)
        rc = run(f)
        f.write(f"retry exit={rc}\n")
        f.flush()
    f.write(f"=== {datetime.datetime.now():%F %T} end ===\n")

if rc != 0:
    print(f"REMIND_FAIL exit={rc} - xem log: {LOG}")
sys.exit(rc)