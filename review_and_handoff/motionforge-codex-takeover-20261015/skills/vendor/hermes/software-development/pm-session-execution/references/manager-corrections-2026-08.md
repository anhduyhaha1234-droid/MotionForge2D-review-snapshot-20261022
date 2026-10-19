# Manager-lane corrections & patterns (S09 full sprint + C1 + C2 fast-tracks, 2026-08)

Session-specific detail backing pm-session-execution. Condensed from ~40 worker dispatches across 3 correction rounds on MotionForge2D.

## Terminal-state protocol honesty
When the governing prompt says "required metric fail/unknown/FOQ ⇒ terminal MUST be BLOCKED_WITH_FINDINGS", do NOT record TASK_MANAGER_VERIFIED just because every individual task went green. C1 review finding F1 caught exactly this: workers honestly reported FAIL_OPEN_QUESTION (f1_hard_cut, f5_group_occlusion had no measured route), but the manager still wrote VERIFIED. Honest FOQ reporting by workers is correct protocol — and it makes the sprint terminal BLOCKED, not VERIFIED.

## Freeze-manifest handshake (J1-style joins)
- Worker-declared freeze hashes MUST be reproduced by the Manager before accepting. If the log doesn't show how the hash was computed, try standard combos: sha256 over concat of (path_utf8 + b'\0' + file_bytes) per file in listed order was the winning formula when plain concatenation/hex-join didn't match.
- After ANY measured run downstream of a freeze, re-hash the pinned files to detect drift. Drift ⇒ invalidate all downstream runs/decisions, resume the owner that caused it, re-freeze, rerun. Never "fix" by updating the recorded constant.
- Machine-readable manifest (path → SHA-256 JSON) beats prose hashes; pin the manifest's own SHA in the registry too.

## Model-empty hiccup pattern (unstable upstream)
Workers die mid-work with "⚠️ No reply: model returned empty content after retries". Can repeat 3–4×/day. Tactics:
- Always RESUME the exact owner session (never new session) with a prompt that shrinks each round and points at the precise stopping point.
- Instruct workers to "log after every small step" so partial progress survives the next death.
- Verify disk state yourself before writing the resume packet (git diff --numstat, ls output dirs, run the suite yourself) — never trust a dead worker's last narration.

## Session/process discovery on this host
- Map session→task via state.db: `SELECT id FROM sessions WHERE started_at > X` + first user message (`SELECT content FROM messages WHERE session_id=? AND role='user' LIMIT 1`). Log files often omit the session id.
- Liveness = wmic ProcessId=<pid> + log-size delta over 30–90s. MSYS `ps` maps PIDs wrong here; EXIT= lines in dispatch logs are the ground truth, and their absence means the wrapper died with its child.

## Cross-task type errors from in-flight edits
A mypy/type error in task A's file can be caused by task B editing a shared import target in-flight (e.g. PEP 562 `__getattr__ -> object` lazy re-export kills static type of `select_route` imported elsewhere). Attribute first (check what's still RUNNING), re-check after B exits. Fix pattern inside B's write-set: keep runtime `__getattr__`, add `if TYPE_CHECKING:` import branch so static imports keep real types. mypy app --no-incremental must return to 0 errors before final gate.

## Windows temp/basetemp cleanup
pytest basetemp dirs under %TEMP% hit WinError 32 file-locks; rm -rf may need 2–3 passes. Dirs still remaining after final pass are throwaway (OS cleans on reboot) and do NOT block a terminal state. Also: run long regression suites as background procs (>10 min foreground times out); mkdir -p the output dir BEFORE redirecting into it or bash dies instantly.

## Registry discipline across rounds
Keep one registry file per round (S09-C1/C2 style): lock table (task → exact session → proc → write-set → pre-hashes → deps), join conditions, BA decisions quoted verbatim, append-only timestamped log. Reconcile prior-round session ids by name even when Codex flags them as non-compliant — record honestly, don't retroactively legitimize.
