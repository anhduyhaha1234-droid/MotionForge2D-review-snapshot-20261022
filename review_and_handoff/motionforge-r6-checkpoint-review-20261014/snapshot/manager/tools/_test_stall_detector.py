import os, sys, time, json, subprocess, hashlib

RUN = r"C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long"
TOOLS = os.path.join(RUN, "manager", "tools", "dispatch_long.py")
PY = r"C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe"
T = r"C:/Users/Admin/AppData/Local/Temp/mf-stalltest"
os.makedirs(T, exist_ok=True)

# fake hermes via .bat shim placed as "hermes.bat" -> but command is "hermes" (exe name).
# Instead: make fake_hermes.py and a wrapper .cmd named hermes.cmd is resolved only for cmd.
# Simplest robust approach: point dispatch at a python -c child by temporary PATH shim using
# a DIRECTORY with 'hermes.bat' which CreateProcess resolves via PATHEXT (prefer .exe/.com
# then .bat/.cmd). Since real hermes.exe also on PATH, remove its dir from PATH in child env.
FAKE = os.path.join(T, "hermes.bat")

def write_fake(mode, seconds):
    # mode: 'grow' (writes log periodically), 'silent' (writes once then sleeps),
    #        'exit' (exits quickly)
    body = r"""@echo off
set MODE=%s
set SECS=%s
echo FAKE_HERMES_START mode=%%MODE%% > "%%FAKE_LOG%%"
if "%%MODE%%"=="exit" exit /b 7
if "%%MODE%%"=="silent" (
  timeout /t %%SECS%% /nobreak >nul
  exit /b 9
)
rem grow mode: append every 2s until SECS elapsed
set /a N=0
:b
set /a N+=1
echo tick %%N%% >> "%%FAKE_LOG%%"
timeout /t 2 /nobreak >nul
if %%N%% lss %%SECS%% goto b
exit /b 5
""" % (mode, seconds)
    open(FAKE, "w", encoding="ascii").write(body)

def run_case(name, mode, secs, stall_s):
    log = os.path.join(T, "worker_%s.log" % name)
    if os.path.exists(log): os.remove(log)
    write_fake(mode, secs)
    env = dict(os.environ)
    # Prefer our fake dir in front of PATH so 'hermes' resolves to hermes.bat.
    env["PATH"] = T + os.pathsep + env["PATH"]
    env["PATHEXT"] = ".BAT;.CMD;.EXE;.COM"
    env["FAKE_LOG"] = log
    receipt = os.path.join(T, "receipt_%s.json" % name)
    t0 = time.time()
    p = subprocess.run([PY, "-B", TOOLS, "manager/packets/LONG01_W1.md", "MF-DEMO-LONG-01",
                        T, log, receipt, "--resume", "FAKE", "--stall-kill-seconds", str(stall_s)],
                       cwd=RUN, env=env, capture_output=True, text=True, timeout=120)
    dt = time.time() - t0
    r = {}
    if os.path.exists(receipt):
        r = json.load(open(receipt))
    print("CASE %-8s rc_wrapper=%d dt=%.1fs exit_code=%s timed_out=%s log_bytes=%s" % (
        name, p.returncode, dt, r.get("exit_code"), r.get("timed_out"), r.get("log_bytes")))
    print("   stdout:", (p.stdout or "").strip()[:200])
    return r, dt

# Case A: healthy long log for 30s with 5s stall -> must NOT be killed (dt ~30s, timed_out False)
rA, dtA = run_case("grow", "grow", 15, 5)      # 15 ticks*2s=30s runtime
# Case B: silent child 20s with 5s stall -> must be STALL_KILLED (~5-25s, timed_out True)
rB, dtB = run_case("silent", "silent", 30, 5)
# Case C: quick exit -> normal
rC, dtC = run_case("exit", "exit", 1, 5)

okA = (rA.get("timed_out") is False and dtA >= 25 and rA.get("exit_code") == 5)
okB = (rB.get("timed_out") is True and dtB <= 40)
okC = (rC.get("exit_code") == 7 and rC.get("timed_out") is False)

verdict = {"A_healthy_not_killed": okA, "B_silent_stall_killed": okB, "C_normal_exit": okC,
           "A": {"dt": round(dtA,1), "exit": rA.get("exit_code"), "timed_out": rA.get("timed_out")},
           "B": {"dt": round(dtB,1), "exit": rB.get("exit_code"), "timed_out": rB.get("timed_out")},
           "C": {"dt": round(dtC,1), "exit": rC.get("exit_code"), "timed_out": rC.get("timed_out")}}
print(json.dumps(verdict, indent=1))
open(os.path.join(RUN, "manager", "evidence", "HARNESS_TEST_20261007.json"), "w", encoding="utf-8").write(
    json.dumps(verdict, indent=2))
