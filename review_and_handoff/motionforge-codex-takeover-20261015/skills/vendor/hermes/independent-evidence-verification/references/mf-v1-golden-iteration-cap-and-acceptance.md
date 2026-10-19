# Iteration cap, byte-verified acceptance, and a narrow continuation (MF-V1-GOLDEN, 2026-09-17)

Wave: MF-RESKIN-V1, a brand-new visual-reskin wave on a local immutable base
(`2594de06…`), two workers dispatched in parallel. This record covers the
**post-dispatch half**: what the first lane's `exit 0` actually meant, how the
Manager verified the intermediate work, and the continuation packet that shipped
only the remainder.

## 1. The shape of the failure: exit 0, zero deliverables

The dispatch receipt for lane MF-V1-GOLDEN read:

```
exit_code: 0        duration_seconds: 2171.861        (36.2 min)
```

and the log tail ended with a coherent self-authored status block:

```
STATUS: RUNNING — phần lớn lõi golden đã chạy và có số thật, nhưng
fixture/evidence CHƯA đóng gói xong, nên chưa `TASK_SUBMITTED`.
…
I. CÒN LẠI TRƯỚC KHI SUBMIT (chưa làm)
   1. make_references.py (đã viết xong, CHƯA chạy)
   2. write_set_guard.py baseline
   3. copy artifacts to EV/GOLDEN
   4. write_set_guard.py verify
   5. local commit
Tôi dừng ở đây để không nhồi thêm claim chưa có bằng chứng.
```

That reads like a disciplined voluntary stop. It was not. Disk truth:

| Check | Result |
|---|---|
| `EV/GOLDEN` files | **0** |
| `wt-golden` `git status --porcelain` | **0** |
| guard run / commit | none |
| `runtime/golden` files | **195** (fixture, annotations, ledger, 18 tools) |

Root cause, found only in session history:

```
select role, substr(content,1,120) from messages where session_id=? order by id desc limit 5
```

→ a synthetic `user` row: `You've reached the maximum number of tool-calling
iterations allowed. Please provide a final response summarizing what you've
found and accomplished so far, without calling any more tools.`

Mechanism: `hermes -z` runs `agent.max_iterations` (**default 90**, in
`agent/agent_init.py`), no env override; `agent.max_turns: 300` in `config.yaml`
is a different knob and does not raise it. The worker hit the cap mid-package.

**Lesson:** exit 0 + a confident final message is not completion. Verify every
deliverable path, and read the cap marker out of `state.db` before forming a
verdict on *why* the lane stopped.

## 2. Byte-verifying the intermediate work (so the continuation need not redo it)

Manager recomputed the claimed hash rather than trusting it:

```
claimed fixture sha256  7e1627e4c8c2421e77758b48f0c003c23d0b8b2f50fc73bc2118bc6b06cd0dab
sha256sum on disk       7e1627e4c8c2421e77758b48f0c003c23d0b8b2f50fc73bc2118bc6b06cd0dab   MATCH
```

Then read the load-bearing claims out of the fixture itself:

| Claim | How verified |
|---|---|
| freeze `2c558ce1…fa684` over canonical JSON minus `freeze` | present, with explicit `hash_scope` + `canonicalization` |
| 7 windows / **28.0 s**, 1 primary + 6 additional, 1 holdout | `window_set_summary` |
| reference film A/B SHA == pin, identical, **39,634** decoded frames | assertion rows, all `passed: true` |
| scene candidates **208** (>0.45) / **224** (>0.25) | assertion rows — matches the locked profile |
| real SAM 2.1 inference (hiera-large, cuda, 2.184 s, 8 masks) | ledger raw + 7 populated annotation dirs |
| demo→film offset | 900-frame MAE sweep: 0.1536 at +1200 vs 0.445 at ±1, 39.2 at ±300 |

Only after this did "the analysis half is genuinely done" become an actionable
fact rather than a self-report.

## 3. Adopting the worker's correction of the Manager's own packet

The packet said **"book scene frames 450–569"**. The worker tested that literally
in film space, found no match, and returned a `book_window_reconciliation` block:

- `packet_statement`: "book scene frames 450-569"
- `tested_literally_in_film_space`: "no match found"
- `resolved_mapping`: the numbering belongs to the **C11/demo** index space; in
  film canonical space the book window is **frames 1650–1769**
- `proven: true`, with an offset sweep as the evidence artifact

It also independently **disqualified a reference artifact the Manager had
supplied**: the PROTOTYPE_A stills matched neither the film nor the demo at any
offset (best 160×90 MAE 8.04 ≈ no match) ⇒ they are diagnostic-harness output,
never source truth.

Handling: adopt both, record the adoption in the registry, and put an explicit
*"already accepted — do not re-open or re-derive this"* clause in the continuation
so the budget is not spent re-litigating a settled question. A file's name and
location are not provenance — check that a claimed source artifact actually
matches the source before it becomes ground truth for an acceptance row.

## 4. Verifying a claimed capability blocker at the interface

The worker reported vision unavailable, which excused every semantic label
("all labels are structural or come from cross-referenced project records").
Instead of accepting or dismissing it, the Manager probed the same route:

```
POST /v1/chat/completions  { model: <pinned>, messages: [ {type:text}, {type:image_url, url: "data:image/png;base64,<8x8 PNG>"} ] }
→ "…image omitted due no vision support…"
```

The claim was **true**. A blocker reproduced at the boundary is verified; one that
cannot be reproduced is a finding. Corollary recorded for the user: with a
text-only route, no worker in the wave can produce semantic visual approval, so
the visual gate is a human gate — keep evidence structural/numeric and honour the
harness's `human NOT_REVIEWED` marker.

## 5. The narrow continuation

Continuation packet (round 2) contained **only**:

1. Rules-load reminder (short).
2. Manager-verified verdict on round 1 — a table of what was checked and matched.
3. A short **accepted** list: frame-space resolution, PROTOTYPE_A finding, and the
   truthful gaps (hands not separable at 640×360; structural-only labels;
   between-anchor frames not interpolated; occlusion class
   `PARTIAL — NOT_DEMONSTRATED`; z-order `unresolved`).
4. The exact outstanding steps (the worker's own I.1–I.5).
5. Explicit boundary: a sibling task's runtime is **not yours** — do not write
   into it, record the dependency instead.
6. Unchanged write set + the specific gates required to emit `TASK_SUBMITTED`.

It did **not** re-send the contract, the acceptance matrix, or the doc list. When
a lane ends at the iteration cap, the fix is a narrower remainder, not a
smaller-model or a different worker.

## 6. Ownership note

`--resume <sid>` minted a NEW session id for the continuation turn. That is safe
**only** because the round-1 process had already exited (`exit_code: 0` in the
receipt, `ended_at_utc` recorded). Registry records the lineage
(`…_1e9357` dead → `…_1e70db` active) with one writer guaranteed.

## 7. Checklist distilled

- [ ] Exit code 0 verified against **deliverable paths on disk**, not prose.
- [ ] Cap/termination marker read from `state.db` messages before assigning cause.
- [ ] Every worker-claimed hash recomputed by the Manager.
- [ ] Load-bearing numbers read out of the artifact, not quoted from the summary.
- [ ] Worker corrections of the Manager's own packet adopted when evidenced.
- [ ] Claimed capability blockers reproduced at the interface.
- [ ] Accepted work listed explicitly in the continuation ("do not redo").
- [ ] Continuation sized to the remainder, not the whole contract.
