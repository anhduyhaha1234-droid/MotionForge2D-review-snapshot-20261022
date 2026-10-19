# T02 partial-progress connection death — resume-to-finish (DV3-R2, 2026-09-08)

Complement to `dv3-r2-t03-zero-artifact-deaths.md` (deaths with ZERO artifacts → pivot/split the prompt). This case covers death WITH landed progress → resume the same session to finish.

## Signature

- Dispatch log holds exactly one line (`API call failed after 3 retries: Connection error.`) + wrapper EXIT line; session ends `agent_close` well below a working session's count (T02-R2: 37 msgs; last assistant line a fragment, e.g. `Env`).
- BUT disk shows real progress: module file landed (962 lines, `py_compile` OK), fixtures + probes present in the owned runtime roots, frozen write-set manifest still VERIFIED, MAIN DB hash unchanged.
- Missing: the second new file (tests) + REPORT.md + STATUS marker. No REPORT exists at all.

## Decision: resume-to-finish, don't pivot

- The failure is infrastructure (connection error), not prompt shape: the worker was already THROUGH reading and writing. Splitting the prompt gains nothing.
- Per Rules §7: mark `RUNNING_RETRY_WAIT`, wait the full 5 minutes, then resume the SAME owner session with the SAME prompt and SAME model. When the runtime mints a NEW session instead of continuing, adopt the lineage and confirm single active writer (priors terminal `agent_close`).
- T02 needed three connection-death resumes (R1→R2→R3→R4) before landing; each resume preserved prior bytes (the module survived across sessions) and the lane closed with 10 passed + ruff clean.

## Watchdog expiry vs stale fire

- A bounded REPORT-marker watchdog that times out while the worker is merely slow is a normal expiry (exit 2): log END with the fire timestamp and move on.
- A watchdog that fires ON an already-processed REPORT is STALE: compare REPORT mtime against the last-processed marker first, log STALE, do not re-verify blindly.
