# MotionForge2D — root review G2-B2-RECOVER-01

Verdict: **EXACT_INPUT_RECOVERY_APPROVED / G2_MEDIA_BLOCKED**. The isolated vault is approved as a source of three exact historical files, not as a runnable media workspace or accepted video.

Root independently re-ran `python -B -m unittest -v test_recover` (6/6 PASS, exit 0) and enumerated and SHA-256 hashed every file in `C:/Users/Admin/Documents/Codex/g2b2-recovery/vault-g2b2-001/`. The only three files are:

| Relative path | Bytes | SHA-256 |
|---|---:|---|
| `task/corrections/identity/r6/source_actor_ledger.jsonl` | 36,876 | `1012a20a03b10e91a22e1e7a588e4f6b7f8259599f90f0d4fd855bec9f9c3715` |
| `task/corrections/identity/r6/cast_atlas.json` | 4,120 | `e847acb8d30f120bcaffb81b1e5048baf3e32280bcd74e9e5688b20a56149a4e` |
| `task/graph/reuse_bundle/shot_anchor_v1.baseline.api.json` | 16,804 | `0ff8ed9c92441230d76d42f2d3eeffb92e70f1b8749f663b170d1566a3df7f4e` |

Worker receipt `C:/Users/Admin/Documents/Codex/g2b2-recovery/RECEIPT.json` has SHA-256 `d0ff8b2a33b3fd6bacb4839d0c633a0293f8a5a0d70f7f8b3093a4d8e79da70e`, 25 PASS / 1 UNVERIFIED / 0 FAIL. The historical R6 packet manifest binds the ledger and atlas, and three old graph copies share the graph hash. Static graph binding is useful evidence; node API, model loading and output semantics have not been tested. The vault is deliberately outside the G2-PREP-01 pilot, so that pilot's exact 76-file inventory remains intact.

Remaining blockers: all 14 pinned CAST PNGs are absent; the full 54-shot storyboard and input media products are absent; runtime Python and endpoint alignment are absent; live queue/lease ownership is not established. No model inference, render or 300-second G2 media pilot has run. A later task must create a versioned media workspace and independently verify any repin or runtime repair before GPU work.
