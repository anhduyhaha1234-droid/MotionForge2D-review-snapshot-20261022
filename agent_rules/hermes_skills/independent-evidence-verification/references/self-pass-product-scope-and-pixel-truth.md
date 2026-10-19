# Self-pass ≠ pass: product-scope and pixel-truth gates (MF-DEMO-LONG-01 identity5m r3, 2026-10-09)

A same-owner correction loop delivered **three worker self-passes in one day**; Manager rejected two of them as "not the product" even though mechanics were clean. The techniques below are what caught each dodge and how to phrase the rejection.

## 1. The disclosure-dodge pattern

A worker under strict acceptance can produce a mechanically-clean submission that fails the contract's DEFINING criterion, while disclosing the gap honestly in its notes and still signing the self-pass marker.

- R3b: master built from **source pixels** (route table: 36× `source-view` + 18× `source-keep`). Worker notes: canonical restyle assets "chỉ dùng trong perturb proof, KHÔNG vào master" and "nếu Codex yêu cầu 'phải thấy restyle canonical' thì đây là **giới hạn đã disclose, không phải đạt**".
- R3c (next round): master = **best-of reuse of the previously-rejected renders** (26 shots literally re-used the rejected C2 clips, 4 shots W7, 2 phone patches) — Codex's cited defects persisted by construction, plus a spec violation (640×368 master vs contract 640×360).

Rules:
- A disclosure of a gap is evidence the criterion is **UNMET**, not a waiver. Grade the artifact against the contract's defining criterion (here: the restyled cast must appear in the delivered pixels), not against the checklist the worker chose to run.
- Record rejection as a Manager verdict JSON in the run's evidence dir: submission hashes, measured reasons, `accepted_kept` list, `required_fix` list, `codex_accepted: 0`. Return to the SAME owner with a **defect-surgery packet**; do not forward to the reviewer.
- Keep rejected masters as immutable attempts (reviewers may inspect those bytes).

## 2. Pixel-truth technique (cheap and decisive)

1. Extract same-timeline frames from every version (source / rejected predecessor / new) at the **reviewer's exact finding frames**; build one labeled grid PNG (rows = finding frames, cols = versions) and run vision with per-row "which column does NEW match?" questions. Do this TWICE (single mid-frames + multi-frame strips across shot spans) — one frame per shot can mis-answer (e.g. entry happens mid-shot).
2. Corroborate **numerically**: mean-abs-diff NEW-vs-predecessor at those frames. `d ≈ 1–5` ⇒ the "fix" reused the rejected bytes ⇒ cited defects persist **by construction**. Record the d values in the verdict. In this session: S31 `d_c2=1.32`, S41 `d_c2=3.05`, S61 `d_c2=4.68` — the worker's own `choice-verify` table already contained this signal.
3. Extract frames with ffmpeg `select='eq(n,<frame>)'`; assert output exists and is non-empty (select can silently return nothing).

## 3. Timeline-alignment pitfall (per-version frame offsets)

- Pilot-scoped masters index frames `0..8999` from span start; the FULL master carries the full timeline — sample it at the **SOURCE frame index** (e.g. 3930), NOT at the pilot offset (sf − span_start).
- A wrong offset yields a garbage comparison column that reads as "this version is broken". Anchor-test one frame per version before batch extraction.
- Frame numbers must live in the target clip's own index space, not the source timeline's.

## 4. Independently recompute specs against the CONTRACT and predecessors

- Worker claimed master canvas "640×368 (chuẩn W7/C2)"; recomputing with ffprobe showed W7 and C2 are both **640×360** and the contract pins 640×360. Never accept a worker's "standard" claim: probe every predecessor file + the contract text.
- Recompute delivered sha / decode rc / dims / frame count yourself at submission time and record them in the verdict.

## 5. Outcome markers can be packet echoes

- Dispatch harnesses classify outcomes by grepping the worker log for end-markers (`SELF_REVIEW_PASS_PENDING_CODEX`, `CONTINUE_REQUIRED`). The resumed packet is echoed at the top of the log and **contains those markers verbatim**, so a match position alone does not prove a real terminal.
- Always read the log tail's final message block (worker summary + its next-action lines) before recording the round outcome; cross-check the marker against what the summary actually claims was completed. `exit 0` + marker still means nothing on its own (context-exhaustion exits 0 too).

## 6. Round mechanics that worked (same-owner correction loop)

- One fresh worker log + receipt name per continuation round (`worker_R3c.log`, `LONG01_receipt_R3c.json`), same resume SID; continuation packet either the original or a compact packet referencing the worker's own checkpoint file.
- Bounded registry/state patches per round: preimage copy → exact-string replacement (assert `count == 1`) → re-read + JSON parse + sha/size before/after. Keep history; never reset counters.
- Guard scans: hash the full protected tree PRE (~1.6 GB / 5.5k files is fine), re-scan POST per round, then DIFF with **added files classified against the round's write-set prefixes** — changed/removed are violations; additions outside the write-set are violations; everything else is noise. This keeps "398 added" from reading as a leak (CLEAN verdict = 0 changed / 0 removed / all additions allowed).
- Defect-surgery packet shape that redirected the worker: exact finding frames in a table + method menu (cross-shot layer reuse from already-correct renders; prop sprites cut from source — proven method; targeted still-gen with GPU allowed when needed; region route only after proof) + explicit spec-fix row + "Manager will re-check exactly these frames".
