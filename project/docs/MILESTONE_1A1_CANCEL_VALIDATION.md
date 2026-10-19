# Milestone 1A.1 — Cancel Validation

**MotionForge 2D**
**Date:** 2026-07-30

---

## Overview

Job cancellation allows users to stop long-running operations (e.g., SAM2 propagation, render). The mechanism uses a `threading.Event` flag that workers check periodically.

---

## 1. Job State Transitions

A cancellable job follows this state machine:

```
pending → running → completed
                   → failed
                   → cancelling → cancelled
```

| Transition | Trigger | Verified |
|---|---|---|
| `pending` → `running` | Worker starts processing | ✅ |
| `running` → `completed` | All work finishes normally | ✅ |
| `running` → `failed` | Unrecoverable error | ✅ |
| `running` → `cancelling` | `POST /jobs/{id}/cancel` called | ✅ |
| `cancelling` → `cancelled` | Worker acknowledges cancel flag | ✅ |

---

## 2. Worker Cancel Check

Workers check the `is_cancelled()` method at defined checkpoints:

```python
# Inside worker loop
for frame_idx in range(total_frames):
    if self.is_cancelled():
        self.set_state(JobState.CANCELLED)
        return
    process_frame(frame_idx)
```

| Checkpoint | Location | Verified |
|---|---|---|
| Before each frame (propagation) | `propagate_worker` | ✅ |
| Before each frame (render) | `render_worker` | ✅ |
| Before final encode | `render_worker` (post-composite) | ✅ |

---

## 3. Cancel Flag Mechanism

| Component | Detail |
|---|---|
| Flag type | `threading.Event` |
| Set by | `POST /jobs/{id}/cancel` endpoint |
| Checked by | Worker thread via `is_cancelled()` → `event.is_set()` |
| Thread-safe | ✅ Yes (`threading.Event` is inherently thread-safe) |

### API Endpoint

```
POST /jobs/{id}/cancel
```

| Response | Meaning |
|---|---|
| 200 | Job transitioned to `cancelling` |
| 404 | Job not found |
| 409 | Job already completed / cancelled |

---

## 4. SAM2 Cancellation Granularity — Documented Limitation

**Limitation:** SAM2 propagation runs per-frame in a loop. Cancellation is checked **between frames**, not during a single frame's inference.

**Impact:**
- A cancel request during frame N's SAM2 inference will not take effect until frame N completes.
- SAM2 inference per frame takes ~100–200ms, so worst-case latency before cancel takes effect is ~200ms.
- This is acceptable for desktop use; no user-visible hang.

**Not implemented (future work):**
- Callback-based mid-inference cancellation for SAM2.
- GPU memory reclamation on cancel (currently relies on garbage collection).

---

## Test Coverage

| Test | Description | Status |
|---|---|---|
| `test_cancel_pending_job` | Cancel a job before it starts | ✅ Pass |
| `test_cancel_running_job` | Cancel a job mid-execution | ✅ Pass |
| `test_cancel_already_completed` | Cancel returns 409 on completed job | ✅ Pass |
| `test_cancel_already_cancelled` | Cancel is idempotent | ✅ Pass |
