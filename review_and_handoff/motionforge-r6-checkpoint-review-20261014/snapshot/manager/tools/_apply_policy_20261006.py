import os, json, hashlib, time

RUN = r"C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long"
MG = os.path.join(RUN, "manager")
def rd(p): return open(p, "rb").read()
def wr(p, b): open(p, "wb").write(b)
def sha(b): return hashlib.sha256(b).hexdigest()

report = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "patches": []}

def patch(path, old, new, tag):
    b = rd(path)
    ob, nb = old.encode("utf-8"), new.encode("utf-8")
    c = b.count(ob)
    if c == 0 and nb in b:
        print("SKIP (already applied)", tag, os.path.basename(path))
        return
    assert c == 1, "PREIMAGE_COUNT=%d for %s (%s)" % (c, path, tag)
    pre = sha(b)
    b2 = b.replace(ob, nb)
    wr(path, b2)
    post = rd(path)
    assert post == b2, "WRITE_MISMATCH %s" % path
    report["patches"].append({
        "file": os.path.relpath(path, RUN).replace("\\", "/"), "tag": tag,
        "pre_sha256": pre, "post_sha256": sha(post),
        "pre_bytes": len(b), "post_bytes": len(post),
        "pre_lines": b.count(b"\n") + (0 if b.endswith(b"\n") else 1),
        "post_lines": post.count(b"\n") + (0 if post.endswith(b"\n") else 1),
    })
    print("PATCHED", tag, os.path.basename(path), len(b), "->", len(post))

# ---------- dispatch_long.py ----------
dp = os.path.join(MG, "tools", "dispatch_long.py")
patch(dp,
 'API_MODE = "chat_completions"\n',
 'API_MODE = "chat_completions"\n\n'
 '# POLICY 2026-10-06 (user: bo budget tu dat): no total-time / call / candidate / continuation\n'
 '# stop gate. Only real writer termination, user stop, or an out-of-scope blocker ends the task.\n'
 'NO_DEADLINE_STOP_GATE = True\n'
 '# Technical hang guard for ONE invocation (not a task budget): on hit the child is killed and\n'
 '# the Manager checkpoints + resumes the SAME owner session (packet 6).\n'
 'MAX_INVOCATION_S = 6 * 3600\n',
 "dispatch:flag")

patch(dp,
 '    if deadline_epoch is None:\n'
 '        print("REFUSED: --deadline-epoch <epoch> required (absolute deadline, packet \u00a73)")\n'
 '        return 2\n'
 '    remaining = deadline_epoch - time.time()\n'
 '    if remaining <= 0:\n'
 '        print("REFUSED: absolute deadline already passed (remaining=%.1fs)" % remaining)\n'
 '        return 2\n',
 '    if deadline_epoch is None:\n'
 '        print("REFUSED: --deadline-epoch <epoch> required (absolute deadline, packet 3)")\n'
 '        return 2\n'
 '    remaining = deadline_epoch - time.time()\n'
 '    if remaining <= 0:\n'
 '        if NO_DEADLINE_STOP_GATE:\n'
 '            print("NOTE: absolute deadline passed (remaining=%.1fs); policy 2026-10-06 -> continue without stop gate" % remaining)\n'
 '        else:\n'
 '            print("REFUSED: absolute deadline already passed (remaining=%.1fs)" % remaining)\n'
 '            return 2\n',
 "dispatch:deadline-gate")

patch(dp,
 '    max_turns = extra[extra.index("--max-turns") + 1] if "--max-turns" in extra else "400"\n',
 '    # policy 2026-10-06: default raised; per-invocation turn cap is not a task terminal.\n'
 '    max_turns = extra[extra.index("--max-turns") + 1] if "--max-turns" in extra else "1000"\n',
 "dispatch:max-turns-default")

patch(dp,
 '            try:\n'
 '                rc = proc.wait(timeout=remaining)\n'
 '            except subprocess.TimeoutExpired:\n'
 '                timed_out = True\n'
 '                proc.kill()\n'
 '                rc = proc.wait()\n',
 '            wait_timeout = remaining if not NO_DEADLINE_STOP_GATE else MAX_INVOCATION_S\n'
 '            try:\n'
 '                rc = proc.wait(timeout=wait_timeout)\n'
 '            except subprocess.TimeoutExpired:\n'
 '                timed_out = True\n'
 '                proc.kill()\n'
 '                rc = proc.wait()\n',
 "dispatch:wait-no-total-gate")

# ---------- heartbeat_long.py ----------
hp = os.path.join(MG, "tools", "heartbeat_long.py")
patch(hp,
 'STOP_AFTER_S = 7 * 3600\n',
 '# POLICY 2026-10-06 (user: bo budget tu dat): no self-imposed stop gate.\n'
 'STOP_AFTER_S = None\n',
 "heartbeat:remove-7h-stop")

patch(hp,
 '        if now - started > STOP_AFTER_S:\n'
 '            break\n',
 '        if STOP_AFTER_S is not None and now - started > STOP_AFTER_S:\n'
 '            break\n',
 "heartbeat:guard-none")

# ---------- SESSION_REGISTRY.json ----------
rp = os.path.join(MG, "registry", "SESSION_REGISTRY.json")
patch(rp, '"status": "RUNNING"', '"status": "TERMINAL"', "registry:worker-terminal")

# ---------- BUDGET.json (registry) : policy 2026-10-06 ----------
bp = os.path.join(MG, "registry", "BUDGET.json")
b = rd(bp)
report["patches"].append({"file": "manager/registry/BUDGET.json", "tag": "budget:policy-2026-10-06",
    "pre_sha256": sha(b), "pre_bytes": len(b)})
budget = {
  "task": "MF-DEMO-LONG-01",
  "run": RUN,
  "first_dispatch_utc": "2026-10-05T16:43:39.893004+00:00",
  "policy": "2026-10-06-user-no-self-imposed-budget",
  "policy_note": "User 06/10: bo gioi han budget tu dat, tiep tuc den hoan thien. Numeric caps below are OBSERVABILITY COUNTERS ONLY - they are NOT stop gates.",
  "old_caps_are_history": {
    "absolute_deadline_utc": "2026-10-07T16:43:39.893004+00:00",
    "window_hours": 48,
    "note": "kept as historical record only; removed as a stop gate per policy 2026-10-06"
  },
  "stop_gates_removed": [
    "absolute_deadline_48h", "candidate_cumulative_max_10", "video_submissions_980",
    "image_submissions_350", "vision_requests_200", "worker_model_attempts_300",
    "manager_model_attempts_60", "technical_continuations_3", "local_correction_rounds_1",
    "transient_cycles_2", "chunk_submissions_900", "correction_allowance_80"
  ],
  "counters_observability_only": {
    "candidate_cumulative_max_10": 10, "chunk_submissions_N_max": 900,
    "video_submissions_max": 980, "image_submissions_max": 350,
    "vision_requests_max": 200, "worker_model_attempts_max": 300,
    "manager_model_attempts_max": 60, "technical_continuations_max": 3,
    "local_correction_rounds_max": 1, "transient_cycles_max": 2
  },
  "operational_guards_kept": {
    "backoff_minutes": 5, "heartbeat_minutes": 20, "audit_no_progress_minutes": 8,
    "max_invocation_seconds": 21600,
    "note": "request timeout / liveness / GPU1 are hang-detection guards, not task budgets"
  },
  "counts_so_far": {
    "video_submissions": 0, "image_submissions": 0, "vision_requests": 0,
    "worker_model_attempts": "UNKNOWN", "manager_model_attempts": "UNKNOWN",
    "candidate_slots_used": 0, "dispatches": 1, "resumes": 0
  },
  "unknowns_policy": "unknown counts stay UNKNOWN; never transcribed as 0"
}
wb = (json.dumps(budget, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
wr(bp, wb)
report["patches"].append({"file": "manager/registry/BUDGET.json", "tag": "budget:post",
    "post_sha256": sha(wb), "post_bytes": len(wb)})
print("PATCHED budget:policy-2026-10-06", len(b), "->", len(wb))

open(os.path.join(MG, "evidence", "POLICY_CHANGE_20261006.json"), "w", encoding="utf-8").write(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print("REPORT_OK", len(report["patches"]), "entries")
