# Container Decode, Segmented Naming, and Same-Size Tamper Verification

Ground truth verification patterns discovered during production delivery review cycles (MF-DEMO-LONG-01 G1 corrections).

---

## 1. Container & Stream Validation vs Magic Byte Heuristics

### The Pitfall
Heuristics that check file magic headers (e.g., checking if `b"ftyp"` exists in the first 64 bytes) combined with a size floor (`size >= 100_000`) give a false sense of validity. Synthetic or corrupted payloads (such as `b"ftyp" + b"x" * 99996`) pass magic checks and size floors, yet crash video decoders, browser previews, and FFmpeg with `moov atom not found: Invalid data found when processing input`.

### The Verification Rule
Never use header string matching or file size as proof of video validity. Always invoke real container and stream decoders:

```python
import subprocess, json
from pathlib import Path

def validate_evidence_video(path: Path, expected_frames: int | None = None) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size < 1000:
        return False, "file missing or too small"
    try:
        cmd = [
            "ffprobe", "-v", "error", "-count_frames",
            "-show_streams", "-show_format", "-of", "json",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            return False, f"ffprobe error: {res.stderr.strip()}"
        data = json.loads(res.stdout)
        v_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
        if not v_streams:
            return False, "no video streams found"
        if expected_frames is not None:
            nb = v_streams[0].get("nb_read_frames") or v_streams[0].get("nb_frames")
            if nb is not None and int(nb) != expected_frames:
                return False, f"expected {expected_frames} frames, got {nb}"
        return True, "ok"
    except Exception as exc:
        return False, f"validation exception: {exc}"
```

---

## 2. Segmented Naming in Upstream Video Sequences

### The Pitfall
Upstream video blend/render tools (e.g., `Rerender_A_Video/blender/video_sequence.py`) typically index frames by their **global sequence frame index**, not local 1-based indexing for each segment:
- Segment 0 (`beg=1, end=11`): produces `0001.jpg`..`0010.jpg`.
- Segment 1 (`beg=11, end=21`): produces `0011.jpg`..`0020.jpg` (NOT `0001.jpg`..`0010.jpg`).

When unit tests only mock or run segment 0, they pass because global and local indices coincide. Segment 1+ then crashes in production with `missing expected frame 0001.jpg`.

### The Verification Rule
- When verifying multi-segment frame propagation, always test at least one segment with `beg > 1`.
- Verify that the collector expects `[f"{fid:04d}.jpg" for fid in range(beg, end)]`.

---

## 3. Same-Size Hash Tamper in Submission Adapters

### The Pitfall
Submission adapters that only check:
```python
if p.stat().st_size != item["bytes"]:
    return False
```
fail to detect in-place data mutations where the byte count remains unchanged (`b"ABCD"` replaced by `b"WXYZ"`). A corrupted or tampered artifact still gets published as `TASK_SUBMITTED`.

### The Verification Rule
The submission validator must always recompute the cryptographic hash of every artifact against the frozen manifest:
```python
actual_sha = sha256_file(p)
if actual_sha != item["sha256"]:
    print(f"SUBMIT BLOCKED: artifact hash mismatch: {actual_sha} vs {item['sha256']}")
    return False
```
If any hash mismatches, the adapter must exit with non-zero exit code and refuse to write the submission marker.

---

## 4. Failure Boundary Isolation & Stale Manifest Invalidation

### The Pitfall
If failure handling only wraps child subprocess execution (`run_one`), preflight checks (e.g., missing asset keys raising `SystemExit`) or post-merge validation exceptions escape the handler. A previously generated `blend_manifest.json` from an earlier successful run remains intact on disk, causing downstream gates to falsely believe the shot succeeded.

### The Verification Rule
Wrap the complete pipeline from preflight through staging, execution, and merge in a unified boundary:
```python
try:
    # 1. Preflight & key check
    # 2. Staging & child subprocess execution
    # 3. Merge & PIL decode verification
    # 4. Manifest publication
except (Exception, SystemExit) as exc:
    # Immediately unlink stale success artifacts
    if manifest_path.exists():
        manifest_path.unlink()
    # Write durable failure receipt
    record_failure(sid, rc=1, blocked=str(exc))
    raise SystemExit(f"PROPAGATE BLOCK [{sid}] {exc}")
```

---

## 5. Strict Type Parsing in Contracts

### The Pitfall
Standard Python `int(val)` silently coerces:
- `int(43.9)` -> `43` (loss of float precision)
- `int(True)` -> `1` (boolean accepted as frame number)
- `int("43")` -> `43` (unvalidated string input)

This causes schema-violating inputs to pass silently.

### The Verification Rule
In contract parsers, strictly disallow boolean and non-integer types before range validation:
```python
def check_strict_int(val, name, sid=""):
    if isinstance(val, bool) or type(val) is not int:
        raise ValueError(f"{name} must be a strict integer (got {type(val).__name__}={val!r}) in {sid}")
    return val
```

---

## 6. Watchdog Quota Preservation & Error Classification

### The Pitfall
Background auto-nudge daemons that unconditionally ping the CLI every 30 minutes burn user token quota while the task is paused waiting for external reviewer approval. Furthermore, retrying immediately on hard errors (401/403/429) can cause account blocks.

### The Verification Rule
1. **Review State Suppression**: If state is `WAITING_CODEX_REVIEW` or `PENDING_REVIEW`, completely skip model-invoking nudges.
2. **Error Classification (Rules §7)**:
   - Hard errors (quota, credit, auth, 401, 403, 429): Stop immediately, do not retry, and log a durable blocker alert.
   - Transient network errors (502, 503, 504, timeout, disconnect): Wait at least 300 seconds (5 minutes) before a single retry resume.
