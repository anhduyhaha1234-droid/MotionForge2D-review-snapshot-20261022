# Authority-doc edits and PROPOSED_ONLY packet loads

Session: MotionForge2D MF-DEMO-LONG-01 packet load, 2026-10-05. Turn was: read
`HERMES_AUTOPILOT_RULES.md` in full → report `RULES_LOADED` → read Current
execution in `CODEX_PM_HANDOFF.md` + `ROADMAP.md` → preflight → STOP.

## 1. A PROPOSED_ONLY packet authorizes READING, not dispatch

The packet text said plainly: *"Không chạy chỉ vì đọc được file"* (don't run just
because you read the file). Correct terminal state for that turn:

- `RULES_LOADED` + the **path, HEAD, and section list actually loaded** (rules §1
  requires path + HEAD + list of sections — quote §0/§0.1/§0.2/§0.3…§12).
- `PREFLIGHT_OK` with **measured** numbers only (see §4).
- Then **stop**: no RUN created, no worker session minted, no write-set, no render.

Do NOT let "I read a rules file" or "there is a packet on disk" become implicit
authority. Dispatch only on an explicit user command to execute the packet. If a
RUN dir named for today does not yet exist (`mf-delivery-runs/<date>/`), say so —
its absence is proof you have not started.

## 2. Editing PM authority docs when the latest user instruction changes a dependency

When the newest user instruction supersedes a prior one, update the three
authority files without destroying history:

- **Keep the old section, mark it SUPERSEDED.** e.g. `### 0.2. … — user cập nhật
  02/10/2026 (SUPERSEDED bởi §0.3)` plus a 2–3 line supersede note under the
  heading. Do not delete the old text.
- **Add a NEW Current block; relabel the OLD Current as Historical.** In handoff
  and roadmap, insert the new `### Current execution …` / `## Current execution
  overlay …` ABOVE the existing one and rename the existing heading to
  `### Historical execution … (<same date>, scope pin …)` — body bytes untouched.
- **Append a dated bullet** to the governing §section carrying the actual
  instruction (here: the "try more 12s samples" dependency was replaced).
- Snapshot byte preimages BEFORE editing and record sha/before/after/grow.

Legitimate because the packet itself told the Manager to *"ghi scope mới rõ
ràng"* and *"cập nhật lại chính file này"* — that is bounded doc work, still not
production/test/UI/config (rules §2 forbids a Manager writing those).

## 3. Byte-exact replace script — pitfalls that actually bit

Built a Python script that did `txt.replace(old, new, 1)` with an
`assert count == 1` guard, `assert grows`, `open(path,"wb").write(...)`.

**Pitfall A — verify line endings, don't assume CRLF.**
First attempt used `NL = chr(13)+chr(10)` (CRLF) and every anchor matched **0**
times → `SystemExit("ANCHOR COUNT 0 …")`. The files were **LF-only**. The real
check is a byte count, not `grep`:

```python
b = open(path,"rb").read()
print(b.count(b"\r\n"), b.count(b"\r"), b.count(b"\n"))   # → 0 0 464  ⇒ LF-only
```

`grep -c $'\r' file` in git-bash returned **464/464** — apparently "every line has
a CR" — which is a **false positive**: the `$'\r'` did not survive the shell layer
and grep matched every line for a different reason. This is the same class as the
CRLF/`.strip()` traps already in terminal-engineering-discipline (#31/#46/#49).
**Never derive a line-ending decision from a shell `grep -c $'\r'`; count bytes in
Python.**

**Pitfall B — `terminal` heredoc args came back corrupted twice.**
Two `terminal(...)` invocations returned *"tool call arguments were corrupted"*
before running. Workaround that worked: `write_file` the script, then invoke it as
a one-line command `cd <dir> && python -B ./script.py`. No heredoc for scripts
carrying backslashes/quotes/unicode anchors.

**Pitfall C — anchors with leading indentation must include the spaces.**
A body line is `… rõ ràng. Không dùng tên task mới\n  để che chi phí cũ.` — the
second line starts with two spaces. The anchor that worked included the prior
line's tail **and** the exact leading indentation; an unindented version matched 0.

## 4. Preflight report — show MEASURED values, name metadata drift

Emit only what a command actually printed: source SHA + stream metadata (frames,
fps, WxH, video vs audio duration and their ms delta), style/graph SHAs, git
HEADS + `--porcelain` counts, GPU used/free MiB, free RAM GiB, free disk GiB,
Comfy queue depth, open listener ports, and whether today's RUN dir exists.

Hook (Windows): `wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /value`
(workable when the `GlobalMemoryStatusEx` ctypes struct misreads via git-bash).

If a manifest's own metadata field disagrees with disk but the **SHA matches**,
report the mismatch as a non-blocking note, never as a failure: here
`LONG_SOURCE_MANIFEST.json` declared `"bytes":1183` while the file is 1333 B
(CRLF) — the SHA binding is what matters.

## 5. Reopening a stale owner session

A Manager session whose last message was ~4 days before the current turn is
**not** automatically resumable. Flag it for a **context-health audit** per rules
§4 rather than resuming blind, and do not transfer ownership just because it is
old. (This session: `20260930_235002_3ac7f9`, last msg 2026-10-01 09:37Z.)

## See also

`long-scope-run-bootstrap-and-deadline-pinning.md` (same umbrella) — the NEXT turn,
when the user answers a PROPOSED_ONLY load with "làm đi": Manager bootstrap
(hash-gated input snapshots, absolute-deadline epoch pinning, budget/registry
bootstrap, prototype-cost reconciliation, new-Manager takeover vs stale resume).
