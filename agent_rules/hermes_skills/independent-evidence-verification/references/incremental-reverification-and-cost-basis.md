# Incremental re-verification after a supersede chain; cost bases; fresh-worktree before-guard (2026-09-28, MotionForge delivery)

## 1. When a lane supersedes its own artifacts, verify INCREMENTALLY — and prove the chain survived

Measured: a proof lane produced assembly **v1 → v1.1 → v1.2 → v1.3** (each pass fixing exactly one
content defect: wrong per-unit prompt → unit not split at a source cut → segment-specific prompt),
each version written as a NEW file with its own pin JSON (file+sha+span per segment) and the last
marked `role=FINAL_FOR_VERIFY`. The follow-up verification pass did NOT repeat the full audit; its
scope was:

* hash-audit only the **new** artifact set + every sha the updated candidate cites (measured
  7/7 candidate rows, 8/8 segment pins, 13/13 receipt `output_files`);
* **re-audit the WHOLE evidence index anyway** — it is cheap and decisive (measured 323/323 rows,
  0 mismatch, 0 missing after two supersede rounds);
* **re-run the declared rule independently** — a claim like "BOOK window has no cut, OCC cut@102"
  is worth exactly what an independent re-run of the declared threshold rule says;
* **supersede integrity**: old versions still on disk, not overwritten, each with its own pins;
* writer check FIRST (no live writer on the read-only root — see
  `live-writer-and-payload-flaps.md` §1).

Verdict vocabulary: name it `..._VERIFIED_INCREMENTAL`, not a re-statement of the full verdict.

Pitfalls from that pass:

* A receipt file name can differ from what the packet guesses (packet said `P5FIX3_RECEIPT.json`,
  actual `P5FIX3_SEG2_RECEIPT.json`). Glob the prefix, verify by sha, and record the rename as a
  note — not a finding.
* A run-record rebuilt after a crash (`reconstructed: true`) can be cross-checked against receipts
  and index rows, but can never be proven *original*. State exactly that; never upgrade it.

## 2. Cost/throughput claims: audit the BASIS, not just the arithmetic

Every "seconds per output second" number carries three implicit bases. Audit all three before
agreeing or disputing it:

* **Which wall.** One run produced two real walls — collector 2387.78 s vs submit 2394.31 s
  (0.27 % apart) — both true, different instruments. Say which instrument the quoted number came
  from; a candidate quoting the other one is a basis note, not an error.
* **Cold vs warm server.** Never compare a cold run to a warm run and call the delta a code effect
  (see `comfyui-video-model-proof` §3: 596.95 cold vs 38.67 warm s/s on the SAME model).
* **Denominator.** Output seconds RAW vs trimmed (e.g. VACE raw 121 frames / 4.033 s vs the
  declared 120-frame / 4.000 s trim) — name which one the ratio used.

**`accepted_seconds = 0` ⇒ cost per accepted second is `UNDEFINED` — not 0, not ∞.** Keep the
formula visible in the report and refuse to emit a division-by-zero as a number.

Good habit: re-derive each claimed ratio from the receipt fields you can see; when the arithmetic
lands slightly off, record the basis difference instead of calling either side wrong.

## 3. Before-guard baseline for a fresh task worktree (phase gate)

Before dispatching a NEW feature task into a fresh worktree created off the integration SHA,
measure and store (in `manager/guards/<TaskID>_before.json`):

* HEAD sha, branch, porcelain count **before** any writer exists;
* per-path state of the task's write-set: sha256+bytes for existing files, explicit
  `exists: false` for files the task will create;
* a runnable baseline: one import smoke (`python -c "import <pkg>..."`) + the cheapest focused
  suite (measured: `pytest tests/.../public_chain -q` ≈ 18 s → `30 passed, 2 skipped`).

That guard is the only way to later prove "only the allowlisted files changed" and "the pre-existing
tests were green before the writer landed".
