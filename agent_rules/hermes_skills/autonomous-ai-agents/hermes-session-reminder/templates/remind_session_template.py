# Template: cron reminder nudge Hermes session (no_agent script).
# Copy, set SID/MODEL/PROVIDER from state.db, set LOG per session.
# Silent on success (stdout empty); prints REMIND_FAIL + exit!=0 on failure.
import datetime
import subprocess
import sys
import time

HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
SID = "<SESSION_ID>"                # SELECT id FROM sessions WHERE title=... (user cung cap)
MODEL = "<MODEL>"                   # SELECT model FROM sessions WHERE id='...'  (DB = source of truth)
PROVIDER = "<PROVIDER>"             # VD "muse" hoac "custom" (tu model_config.provider)
MSG = "tiếp tục làm việc đi"        # DUNG cum user yeu cau - KHONG kem list/prompt
LOG = r"C:\Users\Admin\AppData\Local\hermes\logs\remind_<tag>.log"  # 1 file / 1 session


def run(logf):
    # -m/--provider BAT BUOC: resume khong -m -> model default profile (sai route)
    cmd = [HERMES, "chat", "-q", MSG, "-r", SID, "-m", MODEL, "--provider", PROVIDER, "-Q"]
    # stdout=logf (KHONG capture_output - nuot response manager)
    return subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode


def now():
    return datetime.datetime.now().strftime("%F %T")


with open(LOG, "a", encoding="utf-8", errors="replace") as f:
    f.write(f"=== {now()} start ===\n")
    f.flush()  # tranh subprocess fd-write xen truoc dong start (thu tu log)
    rc = run(f)
    f.write(f"exit={rc}\n")
    if rc in (1, 2):  # retryable (model/API transient)
        f.write("--- retry after 20s ---\n")
        f.flush()
        time.sleep(20)
        rc = run(f)
        f.write(f"retry exit={rc}\n")
    f.write(f"=== {now()} end ===\n")

if rc != 0:
    print(f"REMIND_FAIL exit={rc} - xem log: {LOG}")
    sys.exit(rc)