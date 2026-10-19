# Verifying artifact claims: paths, digests, and stale footprint statements

Session evidence, 2026-09-23 (MotionForge manager run `mf-core-tool-delivery-20260923`, 7 parallel
lanes). Each item below is a *false verdict the manager almost published*, and the check that
replaced it. All are about verifying a worker's claim, not about the worker's domain.

## 1. Locate a claimed artifact by name glob AND by the claimed hash — a single path guess lies

The lane reported its export clip at
`…/runtime/video14b/output/waveB_m1/clip/final_book4s_m1_decoded119_640x360.mp4`.
A single-path existence check printed **MISSING** — and had been believed, the manager would have
reported a completed lane as having produced nothing.

The file existed, at:
`…/outputs/mf-core-tool-delivery-20260923/20260923T1535Z/NEW/VIDEO14B/waveB_m1/clip/final_book4s_m1_decoded119_640x360.mp4`
— i.e. inside a **stray nested `NEW` directory** in the evidence root (sibling to the correct
`VIDEO14B/`), 1,071,337 B, sha `5C2175AE73056EA6552B7B50432F618F7255A09F7CF9E5C695A870FE22286A6D`.

```python
# locate-then-confirm, instead of trusting a path from a report
for base in (RUNTIME, WORKTREE, EVIDENCE_ROOT):
    for p in base.rglob("*book4s_m1*.mp4"):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        print(p.stat().st_size, h[:24], p, "<== MATCHES CLAIM" if h == CLAIM_SHA else "")
```

Rules:
1. Search by name glob, then confirm by **hashing**; report the real path verbatim.
2. A differing path is a **reporting/layout defect** to disclose, not a nuisance to tidy.
3. **Never move or re-copy already-hashed bytes** into a nicer location — that invalidates every
   manifest, freeze record and guard that points at them.
4. Corollary for the packet you write: when you assert where a file is, say *how you measured it*
   ("measured at 18:14 by glob + sha"), so the next reader re-measures instead of trusting.
5. **The nested `NEW` was the manager's own prompt defect, not worker sloppiness.** Every packet
   defined the evidence root once, as a bold alias line (`**NEW:** <run-root>`), and then instructed
   the lane to put evidence under `NEW/<TASK>/**`. That instruction reads two ways — *the run root's*
   `<TASK>` directory, or *a directory called `NEW` created inside the run root* — and 2 of 7 lanes
   took the second reading. Both spellings ended up holding real hashed bytes. Fix at the source:
   never re-use a bare alias token as a path **segment** after defining it; write the literal
   destination (`<RUN_ROOT>/VIDEO14B/raw/<file>`), or give one worked example of a full path.
6. When two spellings exist, measure **both** locations and log the discrepancy as an incident. The
   path is data a reviewer needs in order to recompute hashes - not a mistake to hide, and not
   something to normalise after the fact.

## 2. A digest you cannot recompute is not evidence

A lane reported its adapter's "canonical graph hash" as `97045d0f5adfb961ae907e3628a2a0a5…`.
Recomputing it the obvious way disagreed:

| method | M1 graph | baseline graph |
|---|---|---|
| raw-byte sha256 | `ff134923db899b3a…` | `7ea87b66569cc629…` |
| LF-normalised sha256 | `1bb1d26cdb2cac0f…` | `5c886b0875dc4bfc…` |
| `json.dumps(sort_keys=True, separators=(",",":"))` | `d33bb57bdf7e7feb…` | `5eb932d7366fa162…` |
| worker's "canonical" | **`97045d0f…` — resolved, see below** | — |

**This one turned out to be reproducible, and the manager was wrong to publish "unreproducible".**
The worker later supplied its canonicalisation and it recomputed exactly:

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
```

The entire discrepancy was `ensure_ascii`. The graph carries **133 non-ASCII characters** (a CJK
negative prompt), and the stdlib default `ensure_ascii=True` escapes them to `\uXXXX`, changing the
bytes of a digest whose *text* looks identical. Rules:
- A digest that will not reproduce is a **question to the owner** ("name the function, its
  separators, its key order, its encoding"), not yet a finding. Ask before writing
  "unreproducible" — asking cost one round-trip; publishing it cost the manager a public correction.
- `ensure_ascii` is the trap that hides best: a canonical-JSON digest over non-ASCII text differs
  from the naive recomputation **only when the payload has non-ASCII**, so the same recipe appears to
  work on ASCII fixtures and to fail on the real artifact.
- Prefer digests that reproduce from the artifact with **stdlib alone**, and always **label the
  method** (raw bytes / LF-normalised / sorted-key-compact + encoding). Label twice when one field
  name carries two different quantities — here the same `file_sha256` key held the LF-normalised
  digest for the new graph and the raw digest for the baseline.
- An unverifiable hash printed beside verified ones **reads as proof**. That is the harm of leaving
  it unresolved — and equally the harm of declaring it unverifiable too early.

## 3. "You wrote nothing / the tree is pristine" is hearsay — measure it at dispatch time

A resume packet asserted `porcelain=0` and "you wrote nothing". At recon, `git status --porcelain`
returned `?? app/schemas/media_engine.py` — 42,003 B, mtime 55 minutes **after** the tree checkout,
docstring naming that exact task. Half the claim (evidence root = 0 files) was true; the worktree
half was false.

Rules:
- At recon, run `git status --porcelain` and compare file **mtimes against the checkout time** to
  date a stray artifact. Disclose the contradiction in the packet itself.
- Neither discard nor trust it: `py_compile` it, `ruff --select F` it, verify every authority it
  cites exists — then keep what is correct and repair what is not.
- A file written just before a crash is **unexecuted** code, so run it first. Here the 1,152-line
  module had a fatal defect that had never once executed (a field named `pts` where the model
  required `pts_start_ticks`/`pts_end_ticks` with `extra="forbid"`), plus a `@property` returning a
  hardcoded `False` — fake logic that only a test run exposes.

## 4. Windows verification steps: build temp paths as native `C:/…`, never `mktemp -d`

Verifying the clip's audio means decoding **both** sides to raw PCM and hashing. Doing it with
`T=$(mktemp -d)` produced, twice:

```
Error opening output /tmp/tmp.XXXX/clip.pcm: No such file or directory
```

The directory existed for bash the whole time; `ffmpeg.exe` cannot write there. The same command
with `C:/Users/<user>/AppData/Local/Temp/…` succeeded immediately and both PCM hashes matched
(`2387eded24366afc…`).

Rule: any path passed to a **Windows binary** (`ffmpeg.exe`, `python.exe`, `git`, node CLIs) —
especially an *output* path — must be a native `C:/…` path. Recognise the signature: "No such file
or directory" on an output path you just created yourself is a **path-translation failure**, not a
missing file and not a permissions problem. Do not go chasing ACLs.

## 5. Reading a worker's self-disclosed incidents

The strongest lanes in this run volunteered their own damage, and the fast triage was to classify
each disclosure rather than accept or dismiss it wholesale:

- **Self-inflicted, already repaired** — a `git archive` probe run that was not byte-equal to HEAD
  (CRLF applied), silently normalising the tree; the worker normalised, re-ran and printed
  per-file sha256/byte/CRLF provenance. Accept, keep as process evidence.
- **Self-inflicted, not yet repaired** — two scratch files left in the tree (`_tmp_dump.py`,
  `_tmp_tpl.py`) plus one probe still present. Correct move: name them in the **next** packet's
  housekeeping section instead of silently deleting another agent's file.
- **Environment junk from the worker's own mistake** — calling a script with an MSYS `/c/...` path
  made `python.exe` create `C:\c\Users\...`; the worker removed it itself. Accept the disclosure,
  and re-check that a stray top-level directory is gone before the final gate.
- **Honest gap** — "I did not open a single frame, and I will not invent a description of how the
  book/hand behave." Nothing to verify; record it as the row staying `NOT_REVIEWED` and export a
  contact sheet so a human can close it.

## 6. A corroborating cross-check that agrees only in AGGREGATE proves nothing — verify the pairing

The manager tried to corroborate a worker's mechanism claim ("the template runs two sampler passes
per prompt, so two renders from one submit is normal") with a count from an *older* log:

> 4 `Prompt executed` lines ↔ 4 "model staged" lines, 1:1 → so N passes per prompt is normal.

Those totals matched. They matched **by coincidence**: re-reading per prompt, that log held **2**
Animate-2 prompts (each with 2 passes ⇒ 2 stage lines each = 4) plus **2** unrelated 4-step
anchor/reference prompts that produced **0** stage lines. Two correct totals lined up while the
mechanism being "confirmed" was not the reason they lined up at all.

Rules:
- Never corroborate a per-item mechanism with an aggregate count. Totals coincide for reasons
  unrelated to the hypothesis; the arithmetic cannot tell "2×2" from "4×1".
- Decompose to the item: one prompt id, and for that id the pass count, the stage lines, and the
  submission count. A mechanism claim needs the **pairing**, not the sum.
- Keep the correction when the worker overturns the manager's own cross-check. Here the conclusion
  ("2 passes/prompt is template behaviour; 1 prompt; `submit_calls=1`") survived, but the manager's
  *argument* for it did not — only the worker's per-prompt read was sound. Write that into the
  packet rather than letting a bad argument stand behind a right answer.
- Same shape elsewhere: "3 files changed and all three grew" is not evidence they grew *because* of
  the edit; "the counts agree" is not evidence they agree *for the reason claimed*.

## 7. Defect shapes to hunt when you execute a crashed round's code

Two lanes in this wave had written ~3.5k lines of never-executed code before dying. Executing it
surfaced **nine** real defects across the two modules, and they collapsed into a small set of
**repeatable shapes** — which is what makes them worth a checklist rather than an anecdote.

Read the first failure count as a *signal*, not a result: one lane's first real run was
`16 failed, 9 passed, 4 errors`, and every one of those 16 was the **same infrastructure bug**, i.e.
the suite had not tested the logic at all. "Failing for the wrong reason" is the thing to look for.

| shape | how it presents | what it silently destroys |
|---|---|---|
| **Swapped predicate arguments** | `is_within(path, root)` where the signature is `(root, path)` — every artifact is rejected as `MISSING` | the whole guard, and it looks like a data problem |
| **Wrong-module import inside a bare `except Exception`** | a helper imported from a sibling module that no longer exports it; the `except` swallows `ImportError` and a fallback wins | every read silently comes from the wrong root; a real `422`/404 hides as "no data" |
| **Green-by-fallback filter** | filtering `state == 'ready'` drops the item that is still staging, so the code proceeds with an **older** artifact | correctness: you get a plausible green from stale inputs |
| **Structurally-zero measure** | a crop taken *inside* the expected bbox while the measured feature (a halo ring) lies *outside* it | the check can never fail — a permanently-0.0 metric that reads as "clean" |
| **Cross-wired inputs** | a check fed another segment's mask | a pass that means nothing; the numbers still look plausible |
| **Constant-valued `@property`** | `is_expired` returns a hardcoded `False` | fake logic; delete it or make it deterministic |
| **Constant-ised flag** | a constructor refuses `publishable=False`, so the flag becomes a constant and legitimate intermediates are forbidden | the contract can no longer express a real state |

Method that found them: `py_compile` → `ruff --select F` → **run the tests** → read *why* each failure
fails (not how many). Then, for each fix, require a **negative control**: the new assertion must FAIL
on the pre-fix bytes. A green suite that has never been seen to fail proves nothing, and in this run
the controls restored the module byte-identical afterwards (`55a423df…`) to show the control itself
did no damage.

Two further rules from the same wave:

- **Separate `wall` from `wait` from `server` time.** A lane's own report conflated them (its
  "33.98 s per second" used `wait_s`); the true figures were `server 162.14 s`, `wait 163.734 s`,
  `wall 164.673 s` for 4.000 s generated. Quote the one you measured and name it.
- **A quoted throughput with `accepted seconds = 0` is not throughput.** Report
  `generated` and `accepted` separately, and write cost-per-accepted-second as **undefined** rather
  than dividing wall time by clip length.
