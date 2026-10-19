# Manager record integrity and the self-gate (MF-RESKIN correction wave, 2026-09-22)

Context: a Manager-led correction wave (3 resumed lanes, one GPU phase, 4 frozen evidence ids).
Every lane's code-verification came back clean. What failed was the **Manager's own paperwork** — twice —
and neither failure was visible until the closing gate was pointed at it. This file is the raw material
for §31 of the skill.

---

## 1. Two wrong session ids, and how the truth was derived

`--resume <parent>` mints a new session id. The next budget of the wave was spent rebuilding the
`parent → actual` map, because **the lanes' own reports were wrong about their own identity**:

| Round | What the paperwork said | Ground truth (`state.db` + process window) |
|---|---|---|
| VIDEO14B b3 | "resumed, no new id" (actual = parent) | parent `20260922_183517_69741c` → actual **`20260922_190127_662ec3`**; session window 19:01:27→19:15:38, receipt duration 855.6 s |
| VIDEO14B b4 | actual = the b3 id | parent `20260922_190127_662ec3` → actual **`20260922_191704_d44c18`**; window 19:17:05→19:29:14, receipt duration 734.2 s |
| closeout attempt 1 | not recorded at all | **`20260922_190023_1dca48`**, killed at 6 tool calls, no receipt, row still `OPEN` |

Derivation used (two independent sources, agreed):

```python
# read-only; mode=ro is what keeps the DB untouched
con = sqlite3.connect("file:C:/Users/<u>/AppData/Local/hermes/state.db?mode=ro", uri=True)
rows = con.execute("""SELECT id, message_count, tool_call_count, started_at, ended_at, end_reason
                      FROM sessions WHERE started_at > ? ORDER BY started_at""", (dispatch_epoch,))
```

Cross-check: each candidate session's `started_at` had to sit at the dispatch launch time, and
`(ended_at - started_at)` had to match the receipt's `duration_seconds`; the first `user` message of the
session had to be the packet text. All three agreeing = the id is proven.

**The lesson is not "trust the DB instead of the worker" — it is that identity is a claim like any other.
`--resume` misattribution is silent: the packet text is right, the process is right, only the id the lane
reports is wrong.**

### The killed session's DB state

`20260922_190023_1dca48`: `ended_at IS NULL`, `end_reason IS NULL`, 10 messages / 6 tool calls, zero
file mutations. It was terminated as a process, so nothing ever wrote `agent_close`. Writing
"agent_close" for it would have been a false claim about a clean close; the registry now says
**still OPEN** and labels the round `KILLED_PRE_WRITE`.

---

## 2. The dispatch ledger: 15 rows for 10 dispatches

The ledger was appended to at dispatch time for the first three rounds, then **back-filled again** during
a later catch-up. Result:

- 4 duplicate rows (COMFY c1, VIDEO14B c1, BENCH c1, VIDEO14B b1);
- one row pointing at `MF-V1-VIDEO14B-b2r.json` — a receipt filename that never existed, because the
  corrected closeout round reused the killed attempt's log/receipt stem;
- the killed attempt itself was missing from the ledger entirely.

Resolution (never rewrite the raw history):

- `manager/dispatch-ledger.jsonl` left as the untouched 15-row append history;
- `manager/dispatch-ledger.reconciled.jsonl` = **10 dispatches + 1 killed row**
  (`receipt: null, outcome: KILLED_PRE_WRITE`), each with `packet_sha256`, `packet_bytes`, `cwd`, `model`,
  `log`, `receipt`, `receipt_exists`, plus the DB-derived `session_started_utc` / `session_ended_utc` /
  `session_end_reason`;
- `manager/DISPATCH_LEDGER_RECONCILIATION.md` with a *raw said X vs ground truth Y* table and the proof
  row for each correction;
- assertions that make the file trustworthy: `receipt files on disk == dispatches`, `unresolved: 0`,
  **every `actual_session` exists in `state.db`**, every completed dispatch's `end_reason == agent_close`.

---

## 3. The self-gate that caught the Manager's own corrupted file

The wave's closing gate (`manager/tools/step5_final_gate.py`, 79 checks, exit 0) verifies, in order:
required deliverables exist and are non-empty; all 11 matrix rows present exactly once; the reconciled
ledger's shape and receipt coverage; registry integrity; **all frozen ids re-hash (194 files, 0 mismatch)**;
the delivered clip's sha equals the frozen value; each worktree's HEAD/parent/clean/unpushed; all engine
ports closed and VRAM idle; MAIN untouched; and **no `QUALITY_ACCEPTED` claim anywhere in the
deliverables**.

Two of its checks were written only because the failure had already happened by hand:

```python
check("registry has no corrupted table rows (no '||')", "\n||" not in reg)
check("registry names every task row",
      all(f"**{t}**" in reg for t in ("MF-V1-COMFY", "MF-V1-VIDEO14B", "MF-V1-BENCH", "Manager")))
```

The cause: three successive fuzzy `patch` calls editing adjacent rows of the registry's markdown table.
Each reported success with a plausible diff; the result had **lost the BENCH row** and **doubled every
surviving row's leading pipe** (`|| MF-V1-COMFY | …`). A grep for the dropped row's content returned 0 and
exposed it. Fix was a full `write_file` of the table from reconciled truth, plus the two assertions above,
plus a *Disclosed Manager errors* section in the file recording both the wrong-parent resume and this
corruption with its cause and fix.

**Generalised:** when a table needs two or more adjacent row edits, rewrite the table; after any table
edit, assert row count + re-grep every row you intended to keep; and make the file's structural integrity
a gate row, because a corrupted deliverable that looks successful is exactly the failure your own gate
exists to catch.

---

## 4. Reusable shape of the self-gate

1. Deliverable presence + non-empty, per required path (printed size, not a boolean).
2. Row/claim completeness: each expected key present exactly once.
3. Structural integrity of your own tables/files (`"\n||"`, expected row keys).
4. Cross-file consistency: every hash/id you cite appears in the file you cite it from; every id exists
   in the authoritative store (`state.db`, freeze manifest).
5. Frozen evidence re-hash: **N files, 0 mismatch**.
6. Artifact-identity: the delivered media's sha equals the frozen value.
7. Repo transport: HEAD, parent, clean porcelain, not pushed (§17 method 4).
8. Environment end-state: engine ports closed, VRAM idle, orchestrator processes alive.
9. Protected authority untouched (HEAD + porcelain count of the protected repo).
10. No overclaim: zero occurrences of the vocabulary you are not entitled to
    (`APPROVED`/`CLOSED`/`QUALITY_ACCEPTED`) in every user-facing deliverable.

Keep the raw gate output as an artifact (`manager/STEP5_GATE.txt`) with a PASS count and exit code, so
the reviewer can re-run the same script rather than re-reading prose.
