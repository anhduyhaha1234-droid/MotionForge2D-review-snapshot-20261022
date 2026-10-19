# Atomic Stage-Validate-Publish Protocol and True Liveness Guards (2026-10-19)

Lessons and verified patterns from multi-round G1 review corrections (MF-DEMO-LONG-01 / G1-R1).

## 1. Atomic Stage-Validate-Publish Protocol

### The Problem
When producing submission packages, manifests, or quality matrices, writing directly to final publication filenames BEFORE gate validation allows failed or blocked candidates to leak publication artifacts onto disk. If a gate check throws `GateBlock` or exits nonzero after the write, the candidate directory still contains a fresh manifest or matrix, misleading automated auditors into evaluating unvalidated files.

### The Verified Pattern
Always stage publication artifacts into temporary siblings, validate the gate on the staged data, and atomically publish only upon a verified gate pass:

```python
matrix_tmp = ns_dir / "R6_MATRIX_EVIDENCE.json.tmp"
manifest_tmp = ns_dir / "R6G_MANIFEST.json.tmp"
matrix_final = ns_dir / "R6_MATRIX_EVIDENCE.json"
manifest_final = ns_dir / "R6G_MANIFEST.json"

# 1. Stage
matrix_tmp.write_text(json.dumps(matrix_payload, indent=1), encoding="utf-8")
manifest_tmp.write_text(json.dumps(manifest_data, indent=1), encoding="utf-8")

try:
    # 2. Validate gate on staged content
    verdicts = {q: v["verdict"] for q, v in rows.items()}
    gate_batch_conformance({"matrix": verdicts, "artifacts": manifest_data.get("items", [])}, mode=batch_mode)
    
    # 3. Publish atomically
    shutil.move(str(matrix_tmp), str(matrix_final))
    shutil.move(str(manifest_tmp), str(manifest_final))
except Exception as exc:
    # Clean up immediately on any gate failure
    if matrix_tmp.exists():
        matrix_tmp.unlink()
    if manifest_tmp.exists():
        manifest_tmp.unlink()
    raise exc
```

### Self-Referential Manifest Exclusion
When building recursive directory manifests, always exclude the manifest file itself (e.g. `p.name == "R6G_MANIFEST.json"` or `rel.endswith(".tmp")`) from the item enumeration. Storing the manifest's own hash inside the manifest causes an invalidation cycle or stale self-hash.

---

## 2. True Productive Liveness vs. Bookkeeping Inflation

### The Problem
A monitoring heartbeat that inspects directory `os.path.getmtime` can falsely report `ACTIVE` if it scans bookkeeping files modified by the monitoring loop itself:
- `STATE.json` touched by state updates
- Daemon log files (`telegram_heartbeat.log`, `remind_motionforge.log`)
- Temporary `.tmp` or scratch artifacts

This creates false liveness where the monitor claims active implementation progress while the coding worker is completely idle or stalled.

### The Verified Pattern
Explicitly filter out self-written logs and state records from the liveness scan:

```python
for root, _, files in os.walk(directory):
    if "logs" in root or "preimages" in root:
        continue
    for f in files:
        # Exclude bookkeeping files to prevent self-touch liveness inflation
        if f in ("STATE.json", "telegram_heartbeat.log", "remind_motionforge.log") or f.endswith(".tmp"):
            continue
        if f.endswith((".py", ".json", ".patch", ".md")):
            p = os.path.join(root, f)
            mt = os.path.getmtime(p)
            if mt > latest_mtime:
                latest_mtime = mt
                latest_file = p
```

---

## 3. Review-State Quota Preservation in Watchdogs

### The Problem
Background watchdogs configured to nudge idle agent sessions via CLI resume (`hermes chat -q "tiếp tục làm việc đi" -r <SID>`) will continue nudging every 30 minutes while a task is waiting for external review (e.g. `WAITING_CODEX_REVIEW`). This burns LLM context windows, token quotas, and rate limits without producing usable output.

### The Verified Pattern
Check the authoritative project state before issuing any wake-up or resume command:

```python
def is_waiting_codex_review() -> bool:
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            st = json.load(f)
            return st.get("status") in ("WAITING_CODEX_REVIEW", "PENDING_CODEX_REVIEW")
    except Exception:
        return False

# In watchdog loop:
if is_waiting_codex_review():
    log("State is WAITING_CODEX_REVIEW -> Model nudge skipped to preserve quota.")
    continue
```

---

## 4. Canonical Event Time Indexing & Bounds Rejection

### The Problem
Using dual time conventions (0-based `f` vs 1-based `frame`) without a centralized contract leads to:
1. Default fallback errors: e.g. `e.get('f', 1) + 1` evaluating an input `{"frame": 43}` to `1 + 1 = 2` because `"f"` was missing.
2. Silent out-of-range coercion: e.g. An event at frame 700 in a 50-frame clip being accepted and clamped rather than rejected.
3. Negative contact intervals (e.g. `from = -10`) silently accepted.

### The Verified Pattern
Centralize event parsing into an explicit contract with strict bounds checking:

```python
def parse_event_fid(e: dict, n: int, sid: str = "") -> int:
    f_val = e.get("f")
    frame_val = e.get("frame")
    if f_val is not None and frame_val is not None:
        if int(f_val) + 1 != int(frame_val):
            raise ValueError(f"conflicting event f ({f_val}) vs frame ({frame_val}) in {sid}")
    if frame_val is not None:
        fid = int(frame_val)
    elif f_val is not None:
        fid = int(f_val) + 1
    else:
        raise ValueError(f"event record missing f/frame in {sid}")
    if fid < 1 or fid > n:
        raise ValueError(f"event fid {fid} out of range [1, {n}] in {sid}")
    return fid
```

Reject invalid or negative intervals at the boundary rather than returning empty sets or silent clamps.
