# Long-scope Manager dispatch (MF-DEMO-LONG-01, 2026-10-05)

Proven while opening a full-source video scope (`MF-DEMO-LONG-01`, one 22-min
source, one worker, one main assembly) from a user-dispatched `PROPOSED_ONLY`
packet. Complements the short-scope recipes in
`pm-session-execution/references/hermes-cli-dispatch-and-verify.md`.

## 1. "Đọc packet" ≠ "thực thi packet"

A packet may be `PROPOSED_ONLY`. The read/preflight turn and the dispatch turn are
SEPARATE: on the read turn do only `RULES_LOADED` + live preflight and say plainly
that nothing was dispatched. Dispatch only on the user's explicit "làm đi / thực
thi nguyên packet". Jumping straight from "read the packet" to spawning workers is
a role/authority violation.

## 2. Takeover when the previous Manager is stale

Compute real idle time before deciding to resume:

```python
# read-only
cur.execute("SELECT MAX(timestamp) FROM messages WHERE session_id=?", (sid,))
idle_h = now_utc - datetime.utcfromtimestamp(ts)
```

Rule used: previous Manager `20260930_235002_3ac7f9` (505 msgs, last activity
~100 h earlier) was NOT resumed; this session took over as a NEW Manager, and the
registry records `previous_manager`, `previous_manager_recoverable`,
`previous_manager_last_activity_utc` and `zero concurrent controller`. Never
resume a Manager whose context is 4 days stale just because it is still
technically resumable — that is a context-health call, and the rules let you
make it, but you must WRITE the evidence.

## 3. RUN setup is one deterministic script

One script creates the tree, copies every locked input into the worker write zone
`D/`, and **hashes the copy against the pinned hash** (hash-of-copy, not just
hash-of-source), then writes `BUDGET.json` / `SESSION_REGISTRY.json` /
`PROTOTYPE_COST_RECONCILED.json` and appends to the ledgers. Abort on any input
mismatch (`INPUT_GATE_FAILED`) before a worker exists. `D` layout that worked:

```
RUN/manager/{tools,packets,registry,evidence}
RUN/tasks/<TASK>/{source,style,graph,scripts,cache,env,evidence,output,temp,user}
```

Prototype cost reconciliation is mandatory and is not the new run's budget: emit
`dispatches/terminals/candidate_slots/video_submissions/image_submissions`, mark
the old deadline `EXPIRED (…); NOT revived`, keep the old owner id, and leave
unknown model-attempt counts as the literal string `"UNKNOWN"` — never `0`.

## 4. Harness defects to fix BEFORE the first dispatch

Both were real defects in the prior run's launcher/monitor:

1. **Per-invocation timeout instead of remaining-to-absolute-deadline.** The old
   `dispatch_w2.py` hardcoded `DEADLINE_SECONDS = 21600` for every invocation, so
   each resume silently renewed a 6 h window. New launcher takes
   `--deadline-epoch <epoch>` = the run's one absolute deadline and computes
   `remaining = deadline - now()`; **refuse when `remaining <= 0`**.
   Dry-check it: run with `--deadline-epoch 1` and require
   `REFUSED: absolute deadline already passed` + rc=2. Do this before the real
   dispatch — a launcher that cannot refuse is not a deadline.
2. **Liveness by machine-wide process name.** The old `heartbeat_w2.py` counted
   `tasklist "hermes.exe"` and subtracted 1, so a GUI Hermes with the worker
   already dead read as alive. New monitor reads the dispatch ledger for
   `child_spawned` rows whose launcher has no later `terminal` row and probes
   THOSE exact pids. Prove it on the live run: note `hermes_exe_machinewide` in
   the heartbeat row but drive `worker_alive_exact` off the pid list.

Also keep in the launcher: caller-side `fallback OFF`, packet size guard
(`> 28000 bytes` refuse — Windows argv ceiling), and a receipt that states
"exit code alone is NOT completion proof".

## 5. Resolve the worker's REAL session id by content, not by order

`hermes chat -q … --pass-session-id` mints the id; do not guess it from dispatch
order. Match the packet's first line against each candidate session's FIRST user
message and keep the newest match:

```python
head = open(packet).read().split("\n",1)[0][:40]
for sid, started, model in newest_sessions:          # ORDER BY started_at DESC
    first = first_user_message(sid)
    if head in " ".join(first.split()): resolve(sid); break
```

Write `actual_session_proven_by` into the registry row so a reviewer can
re-derive it (shared/merged packets destroy this proof — one packet file per
task per round).

## 6. Byte-exact edits to PM authority files (rules / handoff / roadmap)

These files sit in a git repo where **`git status --porcelain` is almost always
non-empty** (hundreds of dirty entries), so do NOT read "file is modified" as "my
edit landed". Instead: snapshot the preimage, assert the anchor is unique, assert
the file GREW, re-read to confirm the new text, and re-assert the OLD headings
still exist exactly once.

**Newline gotcha (measured):** in git-bash, `grep -c $'\r' file` reported
`crlf_lines=464/464` for a file whose actual byte content was `CR=0, CRLF=0` —
the shell test lied. Decide the newline convention from a **Python byte count**
(`data.count(b"\r")`, `data.count(b"\r\n")`), then build the replacement with the
matching terminator. Assuming CRLF here would have inserted `\r\n` into an
LF-only file (silent whole-file churn). All three PM docs were LF-only.

When a docs edit is a scope change (user swaps a dependency, marks a section
superseded), write it in the same style as the surrounding authority: a dated
bullet in the operative section, plus a `SUPERSEDED bởi §X` marker on the old
section — and record before/after sha + bytes + line counts in an
`AUTHORITY_EDIT_*.json` next to the preimages.

## 7. Budget pinning + ETA honesty

Pin, before dispatch: N chunk submissions, `K = min(80, ceil(0.10*N))`, video cap
`N+K`, image cap, vision cap, worker/Manager model-attempt caps (after subtracting
attributable prototype spend, unknowns stay UNKNOWN), technical-continuation cap,
and ONE absolute deadline (`first_dispatch + 48h`) that is a HARD STOP, not an ETA.

Derive ETA from a **measured** throughput on this machine, never from a
zero-window/benchmark number. Worked example: WAN Animate2 INT8 at 640×360 ≈
**33.7 s GPU per 1 s of video** (warm ~38.7 s/s) ⇒ 120 s clip ≈ 68 min; 22-min
source ≈ 12–14 h GPU + assembly/QC. Report ETA as a dated milestone table
(`+07` anchor, per-milestone ETA, and the arithmetic that produced it), and state
the risks that would push it (OOM ⇒ more/smaller chunks; anchor rework).

## 8. Do not "fix" the old scope to unblock the new one

The prototype's owner, RUN, ledger and expired deadline stay untouched
(read-only lineage). A new scope gets exactly ONE new worker session; every
shot/chunk/correction/continuation in it resumes that same session. If the worker
hits a route/capability gap (e.g. the vision tool not receiving the image) it must
diagnose within the pinned route and NOT switch provider/model/global config to
route around it; report a real blocker instead.
