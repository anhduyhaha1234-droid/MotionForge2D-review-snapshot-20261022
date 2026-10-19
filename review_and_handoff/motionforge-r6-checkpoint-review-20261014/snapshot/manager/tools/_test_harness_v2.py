"""Offline fixture suite v2 for the dispatch/heartbeat harness (packet §4).

Covers, with NO GPU and NO new render (fake children only):
  A. exit0 + context-error text -> CONTEXT_EXHAUSTED (not completed)
  B. conhost / PID-reuse -> identity check, not bare pid
  C. receipt resolved at RUN/manager/LONG01_receipt_*.json (never manager/manager)
  D. worker LLM terminal BUT render worker still alive (separate flags)
  E. no respawn when there is nothing to do (no new processes)
  F. checkpoint -> continuation argv carries the exact SAME --resume SID
  G. stall-kill A/B/C regression (from _test_stall_detector.py)

usage: python -B manager/tools/_test_harness_v2.py
writes manager/evidence/HARNESS_V2_TEST_20261007.json
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

RUN = Path(r"C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long")
PY311 = r"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe"
EV = RUN / "manager" / "evidence"
T = Path(r"C:/Users/Admin/AppData/Local/Temp/mf-harness-v2")
RESULTS: dict = {}


def rec(key, ok, detail):
    RESULTS[key] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL "), key, "-", detail)


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_tree(name: str) -> Path:
    root = T / name
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    (root / "manager" / "tools").mkdir(parents=True)
    (root / "tasks" / "MF-DEMO-LONG-01" / "output" / "chunks_r2").mkdir(parents=True)
    (root / "tasks" / "MF-DEMO-LONG-01" / "work").mkdir(parents=True)
    shutil.copyfile(RUN / "manager" / "tools" / "heartbeat_long.py", root / "manager" / "tools" / "heartbeat_long.py")
    shutil.copyfile(RUN / "manager" / "tools" / "dispatch_long.py", root / "manager" / "tools" / "dispatch_long.py")
    # minimal D fixtures
    (root / "tasks" / "MF-DEMO-LONG-01" / "state_gate.json").write_text(
        json.dumps({"gate": "RENDER_ALLOWED", "armed_range": ["S0001", "S0002"]}), encoding="utf-8")
    (root / "tasks" / "MF-DEMO-LONG-01" / "chunk_plan.json").write_text(
        json.dumps({"chunks": [{"unit_id": "S0001", "frames": 10}, {"unit_id": "S0002", "frames": 10}]}),
        encoding="utf-8")
    (root / "tasks" / "MF-DEMO-LONG-01" / "output" / "chunks_r2" / "S0001.mp4").write_bytes(b"x" * 10)
    (root / "tasks" / "MF-DEMO-LONG-01" / "worker_fake.log").write_text("fake log\n", encoding="utf-8")
    return root


def write_ledger(root: Path, rows):
    with open(root / "manager" / "DISPATCH_LEDGER.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def run_hb(root: Path):
    p = subprocess.run([PY311, "-B", str(root / "manager" / "tools" / "heartbeat_long.py"), "--once"],
                       cwd=str(root), capture_output=True, text=True, timeout=300)
    rows = []
    hb = root / "manager" / "HEARTBEAT.jsonl"
    if hb.exists():
        rows = [json.loads(l) for l in hb.read_text(encoding="utf-8").splitlines() if l.strip()]
    return p, (rows[-1] if rows else None)


def python_pids():
    r = subprocess.run(["wmic", "process", "where", "name='python.exe'", "get", "ProcessId", "/format:list"],
                       capture_output=True, text=True, errors="replace", timeout=60)
    out = set()
    for line in (r.stdout or "").replace("\r", "").splitlines():
        if line.startswith("ProcessId="):
            try:
                out.add(int(line.split("=", 1)[1]))
            except ValueError:
                pass
    return out


def main():
    T.mkdir(parents=True, exist_ok=True)
    hb_src = RUN / "manager" / "tools" / "heartbeat_long.py"
    dl_src = RUN / "manager" / "tools" / "dispatch_long.py"

    # ---------- A: exit0 + context error => CONTEXT_EXHAUSTED ----------
    dl = load_mod(dl_src, "dl_src")
    log1 = T / "ctx_err.log"
    log1.write_text("...\nHTTP 400: This model's maximum context length is 1048576 tokens.\n"
                    "Context length exceeded, but provider did not report one.\n"
                    "Max compression attempts (3) reached.\n", encoding="utf-8")
    c1 = dl.classify_outcome(str(log1), 0)
    rec("A_exit0_context_error", c1["class"] == "CONTEXT_EXHAUSTED" and c1.get("not_completed") is True,
        "class=%s not_completed=%s" % (c1["class"], c1.get("not_completed")))
    log2 = T / "trunc.log"
    log2.write_text("... Response truncated due to output length limit ...\n", encoding="utf-8")
    rec("A2_truncated", dl.classify_outcome(str(log2), 0)["class"] == "OUTPUT_TRUNCATED",
        dl.classify_outcome(str(log2), 0)["class"])
    log3 = T / "continue.log"
    log3.write_text("checkpoint written\nCONTINUE_REQUIRED: block 12 next\n", encoding="utf-8")
    rec("A3_continue_required", dl.classify_outcome(str(log3), 0)["class"] == "CONTINUE_REQUIRED",
        dl.classify_outcome(str(log3), 0)["class"])
    log4 = T / "clean.log"
    log4.write_text("all good, final answer\n", encoding="utf-8")
    rec("A4_exit0_no_marker_labeled", dl.classify_outcome(str(log4), 0)["class"] == "EXIT0_NO_KNOWN_MARKER",
        dl.classify_outcome(str(log4), 0)["class"])

    # ---------- B: identity, not bare pid (conhost / PID reuse) ----------
    hb_mod = load_mod(hb_src, "hb_src")
    me = os.getpid()
    facts = hb_mod.proc_facts(me)
    b1 = (facts is not None and bool(facts)) and hb_mod.identity_alive(me, facts["created"], facts["name"]) is True
    b2 = hb_mod.identity_alive(me, "19990101000000.000000+000", facts["name"]) is False
    b3 = hb_mod.identity_alive(me, facts["created"], "conhost.exe") is False
    b4 = hb_mod.identity_alive(999999998) is False
    rec("B_identity_alive_exact", b1, "same pid+created+name -> True")
    rec("B2_pid_reuse_wrong_creation", b2, "same pid, wrong creation -> False (PID reuse)")
    rec("B3_conhost_name_mismatch", b3, "same pid+created, wrong exe -> False (conhost)")
    rec("B4_dead_pid", b4, "nonexistent pid -> False")

    # ---------- C: receipt path is RUN/manager (never manager/manager) ----------
    rootC = build_tree("heartbeat_receipt")
    (rootC / "manager" / "LONG01_receipt_T.json").write_text(
        json.dumps({"exit_code": 0, "timed_out": False, "note": "fixture"}), encoding="utf-8")
    decoy = rootC / "manager" / "manager"
    decoy.mkdir(parents=True, exist_ok=True)
    (decoy / "LONG01_receipt_T.json").write_text(json.dumps({"exit_code": 99}), encoding="utf-8")
    missing = str(rootC / "manager" / "LONG01_receipt_MISSING.json")  # dispatch row points at a missing path
    write_ledger(rootC, [
        {"action": "dispatch", "task_id": "T", "at_utc": "2026-10-07T00:00:00Z", "launcher_pid": 11111,
         "receipt": missing, "log": "tasks/MF-DEMO-LONG-01/worker_fake.log", "round": "T.md"},
        {"action": "terminal", "task_id": "T", "at_utc": "2026-10-07T01:00:00Z", "launcher_pid": 11111,
         "receipt": missing, "receipt_note": "closes by launcher_pid"},
    ])
    p, row = run_hb(rootC)
    rec("C_receipt_path_manager_not_manager_manager",
        bool(row) and row["invocation"]["receipt"] is not None
        and str(row["invocation"]["receipt"]).replace("\\", "/").endswith("/manager/LONG01_receipt_T.json")
        and "/manager/manager/" not in str(row["invocation"]["receipt"]).replace("\\", "/"),
        "receipt=%s" % (row or {}).get("invocation", {}).get("receipt"))
    rec("C2_closed_invocation_flags",
        bool(row) and row["llm_worker_alive"] is False and row["controller_alive"] is False
        and row["invocation"]["open"] is False,
        "llm=%s ctl=%s open=%s" % ((row or {}).get("llm_worker_alive"), (row or {}).get("controller_alive"),
                                   (row or {}).get("invocation", {}).get("open")))
    rec("C3_outcome_from_receipt_no_marker", bool(row) and row["outcome"]["class"] == "EXIT0_NO_KNOWN_MARKER",
        (row or {}).get("outcome", {}).get("class"))
    rec("C4_pending_work_next_shot", bool(row) and row["pending_work"]["next_missing"] == "S0002"
        and row["pending_work"]["chunks_done"] == 1,
        "%s" % (row or {}).get("pending_work"))

    # ---------- D/E: render still alive after LLM terminal; no respawn ----------
    pre = python_pids()
    # open invocation whose child identity does NOT match (bogus creation) -> DEAD, not alive
    sleeper = subprocess.Popen([PY311, "-c", "import time; time.sleep(150)"])
    time.sleep(1.5)
    sleep_facts = hb_mod.proc_facts(sleeper.pid)
    rootD = build_tree("heartbeat_open")
    lp_pid = sleeper.pid  # use a live pid as "launcher" with recorded identity = bogus creation
    write_ledger(rootD, [
        {"action": "dispatch", "task_id": "T", "at_utc": "2026-10-07T02:00:00Z", "launcher_pid": lp_pid,
         "receipt": str(rootD / "manager" / "LONG01_receipt_L.json"),
         "log": "tasks/MF-DEMO-LONG-01/worker_fake.log", "round": "L.md"},
        {"action": "child_spawned", "task_id": "T", "at_utc": "2026-10-07T02:00:01Z", "child_pid": lp_pid,
         "launcher_pid": lp_pid, "child_created": "19990101000000.000000+000", "child_name": "python.exe"},
    ])
    p1, row1 = run_hb(rootD)
    rec("D_bogus_identity_not_alive",
        bool(row1) and row1["invocation"]["open"] is True and row1["llm_worker_alive"] is False
        and row1["outcome"]["class"] == "INVOCATION_OPEN" and row1["render_worker_alive"] is False,
        "open=%s llm=%s outcome=%s render=%s" % ((row1 or {}).get("invocation", {}).get("open"),
                                                 (row1 or {}).get("llm_worker_alive"),
                                                 (row1 or {}).get("outcome", {}).get("class"),
                                                 (row1 or {}).get("render_worker_alive")))
    # rewrite same ledger with the REAL creation of the live pid -> identity matches -> alive
    write_ledger(rootD, [
        {"action": "dispatch", "task_id": "T", "at_utc": "2026-10-07T02:00:00Z", "launcher_pid": lp_pid,
         "receipt": str(rootD / "manager" / "LONG01_receipt_L.json"),
         "log": "tasks/MF-DEMO-LONG-01/worker_fake.log", "round": "L.md"},
        {"action": "child_spawned", "task_id": "T", "at_utc": "2026-10-07T02:00:01Z", "child_pid": lp_pid,
         "launcher_pid": lp_pid, "child_created": sleep_facts["created"], "child_name": sleep_facts["name"]},
    ])
    p2, row2 = run_hb(rootD)
    rec("D2_matching_identity_is_alive",
        bool(row2) and row2["llm_worker_alive"] is True and row2["controller_alive"] is True,
        "llm=%s ctl=%s" % ((row2 or {}).get("llm_worker_alive"), (row2 or {}).get("controller_alive")))

    # render worker alive while LLM terminal: fake runner process with 'p4_wan_run' in cmdline
    runner = subprocess.Popen([PY311, "-c", "import time; print('fake p4_wan_run offline'); time.sleep(120)"])
    time.sleep(1.5)
    p3, row3 = run_hb(rootC)
    rec("D3_render_alive_after_llm_terminal",
        bool(row3) and row3["llm_worker_alive"] is False and row3["render_worker_alive"] is True,
        "llm=%s render=%s detail=%s" % ((row3 or {}).get("llm_worker_alive"),
                                        (row3 or {}).get("render_worker_alive"),
                                        (row3 or {}).get("render_detail")))
    runner.kill(); runner.wait()

    # E: no respawn — heartbeat runs add no processes, ledger untouched
    led_before = (rootC / "manager" / "DISPATCH_LEDGER.jsonl").read_bytes()
    p4, _ = run_hb(rootC)
    led_after = (rootC / "manager" / "DISPATCH_LEDGER.jsonl").read_bytes()
    sleeper.kill(); sleeper.wait()
    time.sleep(0.5)
    post = python_pids()
    rec("E_no_respawn_no_new_python",
        (post == pre) and (led_before == led_after) and p4.returncode == 0,
        "pid-diff=%s ledger_unchanged=%s" % (sorted(post - pre), led_before == led_after))

    # ---------- F: continuation argv carries the exact SAME --resume SID ----------
    fake = T / "fakebin"
    fake.mkdir(parents=True, exist_ok=True)
    fake_py = fake / "fake_hermes.py"
    fake_py.write_text(
        "import os, sys, time\n"
        "argv_out = os.environ.get('FAKE_ARGV_OUT')\n"
        "if argv_out:\n"
        "    open(argv_out, 'w', encoding='utf-8').write(' '.join(sys.argv))\n"
        "log_out = os.environ.get('FAKE_LOG_OUT')\n"
        "mode = os.environ.get('MODE', '')\n"
        "err = os.environ.get('FAKE_ERR', '0')\n"
        "fh = open(log_out, 'a', encoding='utf-8') if log_out else None\n"
        "def w(s):\n"
        "    if fh:\n"
        "        fh.write(s + '\\n'); fh.flush()\n"
        "w('FAKE_HERMES_START mode=%s err=%s' % (mode, err))\n"
        "hold = float(os.environ.get('FAKE_HOLD', '0'))\n"
        "if hold:\n"
        "    time.sleep(hold)\n"
        "if mode == 'exit':\n"
        "    sys.exit(7)\n"
        "if mode == 'silent':\n"
        "    time.sleep(20); sys.exit(9)\n"
        "if mode == 'grow':\n"
        "    for i in range(12):\n"
        "        w('tick %d' % i); time.sleep(1)\n"
        "    sys.exit(5)\n"
        "if err == '1':\n"
        "    w('HTTP 400: maximum context length is 1048576 tokens.')\n"
        "    w('Max compression attempts (3) reached.')\n"
        "sys.exit(0)\n", encoding="utf-8")
    # TEST MODE: route the child to the python fake via the supported argv prefix;
    # NEVER let a fixture invoke the real CLI (2026-10-07 incident: a .bat shim is
    # NOT resolved by CreateProcess, so the real hermes.exe on PATH ran instead).
    prefix = json.dumps([PY311, "-B", str(fake_py)])
    rootF = build_tree("dispatch_f")
    (rootF / "packet.md").write_text("fixture packet\n", encoding="utf-8")
    (rootF / "work").mkdir(exist_ok=True)
    env = dict(os.environ)
    env["DISPATCH_TEST"] = "1"
    env["DISPATCH_HERMES_ARGV_PREFIX"] = prefix

    def run_dispatch(receipt_name, extra_args, err="0"):
        argv_out = T / ("argv_%s.txt" % receipt_name.replace(".", "_"))
        log_out = rootF / "tasks" / "MF-DEMO-LONG-01" / ("w_%s.log" % receipt_name.replace(".", "_"))
        env2 = dict(env)
        env2["FAKE_ARGV_OUT"] = str(argv_out)
        env2["FAKE_LOG_OUT"] = str(log_out)
        env2["FAKE_ERR"] = err
        env2["MODE"] = ""
        env2["FAKE_HOLD"] = "2"  # let the dispatch capture child identity (pid+creation) first
        cmd = [PY311, "-B", str(rootF / "manager" / "tools" / "dispatch_long.py"),
               str(rootF / "packet.md"), "MF-DEMO-LONG-01", str(rootF / "work"),
               str(log_out), str(rootF / "manager" / receipt_name), "--stall-kill-seconds", "30"] + extra_args
        p = subprocess.run(cmd, cwd=str(rootF), env=env2, capture_output=True, text=True, timeout=180)
        rec_data = json.loads((rootF / "manager" / receipt_name).read_text(encoding="utf-8"))
        argv = argv_out.read_text(encoding="utf-8", errors="replace").strip() if argv_out.exists() else ""
        return p, rec_data, argv

    pR, rR, argvR = run_dispatch("LONG01_receipt_SID.json", ["--resume", "20261005_235131_0caeab"])
    rec("F_resume_same_sid_in_argv",
        "--resume 20261005_235131_0caeab" in argvR and rR.get("new_session") is False
        and rR.get("resume_session_requested") == "20261005_235131_0caeab",
        "argv=%s..." % argvR[:160])
    rec("F2_defaults_80turns_16k",
        rR.get("max_turns") == "80" and rR.get("max_tokens_requested") == "16384",
        "max_turns=%s max_tokens=%s" % (rR.get("max_turns"), rR.get("max_tokens_requested")))
    led = [json.loads(l) for l in (rootF / "manager" / "DISPATCH_LEDGER.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    term = [r for r in led if r.get("action") == "terminal"][-1]
    spawn = [r for r in led if r.get("action") == "child_spawned"][-1]
    rec("F3_terminal_row_machine_readable",
        term.get("launcher_pid") is not None and term.get("outcome_class") == "EXIT0_NO_KNOWN_MARKER"
        and spawn.get("hermes_max_tokens_env") == "16384" and bool(spawn.get("child_created")),
        "terminal.outcome=%s spawn.env=%s created=%s" % (term.get("outcome_class"),
                                                         spawn.get("hermes_max_tokens_env"),
                                                         bool(spawn.get("child_created"))))

    pN, rN, argvN = run_dispatch("LONG01_receipt_NEW.json", [])
    rec("F4_new_session_no_resume", rN.get("new_session") is True and "--resume" not in argvN,
        "new_session=%s argv=%s..." % (rN.get("new_session"), argvN[:120]))

    pE, rE, argvE = run_dispatch("LONG01_receipt_ERR.json", [], err="1")
    rec("F5_exit0_context_error_not_completed",
        rE.get("outcome_class") == "CONTEXT_EXHAUSTED" and rE.get("outcome_detail", {}).get("not_completed") is True,
        "outcome=%s not_completed=%s" % (rE.get("outcome_class"), rE.get("outcome_detail", {}).get("not_completed")))

    # ---------- G: stall detector regression (A/B/C; same python fake) ----------

    def run_stall(name, mode, stall_s):
        log = rootF / "tasks" / "MF-DEMO-LONG-01" / ("stall_%s.log" % name)
        env3 = dict(env)
        env3["FAKE_LOG_OUT"] = str(log)
        env3["FAKE_ARGV_OUT"] = str(T / ("stallargv_%s.txt" % name))
        env3["MODE"] = mode
        cmd = [PY311, "-B", str(rootF / "manager" / "tools" / "dispatch_long.py"),
               str(rootF / "packet.md"), "MF-DEMO-LONG-01", str(rootF / "work"), str(log),
               str(rootF / "manager" / ("stall_%s.json" % name)),
               "--stall-kill-seconds", str(stall_s), "--max-turns", "80"]
        t0 = time.time()
        p = subprocess.run(cmd, cwd=str(rootF), env=env3, capture_output=True, text=True, timeout=180)
        dt = time.time() - t0
        return json.loads((rootF / "manager" / ("stall_%s.json" % name)).read_text(encoding="utf-8")), dt

    rA, dtA = run_stall("grow", "grow", 5)     # 12 ticks * 1s = ~12s runtime, must NOT be killed
    rec("G_A_healthy_not_killed", rA.get("timed_out") is False and rA.get("exit_code") == 5 and dtA >= 9,
        "dt=%.1f exit=%s timed_out=%s" % (dtA, rA.get("exit_code"), rA.get("timed_out")))
    rB, dtB = run_stall("silent", "silent", 5)  # silent -> killed at ~5-20s
    rec("G_B_silent_stall_killed", rB.get("timed_out") is True and dtB <= 40,
        "dt=%.1f timed_out=%s" % (dtB, rB.get("timed_out")))
    rC, dtC = run_stall("exitx", "exit", 5)
    rec("G_C_normal_exit", rC.get("exit_code") == 7 and rC.get("timed_out") is False and dtC <= 30,
        "dt=%.1f exit=%s" % (dtC, rC.get("exit_code")))

    allok = all(v["ok"] for v in RESULTS.values())
    summary = {"at": time.strftime("%Y-%m-%dT%H:%M:%S+07:00"), "all_pass": allok,
               "cases": RESULTS, "runner": str(Path(__file__)), "label": RESULTS and
               "offline fixtures; no GPU; fake children only"}
    out = EV / "HARNESS_V2_TEST_20261007.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n== HARNESS V2:", "ALL PASS" if allok else "FAILURES PRESENT", "->", out)
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
