# Independent visual verification (manager gate for visual/demo lanes)

Worker green tests + screenshots do NOT prove a visual claim. Before any
visual gate, the manager independently (own terminal calls, own evidence dir):

1. Re-extracts frames with ffmpeg from the pinned source hash — never trusts
   worker-supplied crops. Verifies the frame-index mapping first (e.g. local
   0/60/119 vs source 450/510/569); a wrong-window extract silently "proves"
   nothing. Records which source frames each derivative came from.
2. Computes ROI pixel diffs (numpy/PIL) on the claimed event region AND a
   control region. Byte-identical consecutive frames (mean diff 0.0) kill an
   alleged transition event outright. Static white-pixel share = static edge,
   not pages.
3. Vision-checks BOTH full frames and the worker's evidence strips. Telltales
   of bad worker evidence: strip is tiny (single-digit KB) and does not show
   the claimed object at all (background only); pose claim contradicts pixels
   (chair seat + chair legs under hem + zero bare legs = seated, not
   standing).
4. Cross-checks REPORT metadata against disk: recompute the contract/evidence
   hash (a mismatched hash string = unverified copy-paste); `ls` every file
   the worker claims is "absent" before accepting a required-reading excuse.

Correction goes back to the EXACT task owner with file:line-level findings
and the manager's own numbers (frame pairs, ROI means, white-pixel shares).
Gate stays held until re-verified on fresh worker output.

Resume gotcha (2026-09-08): `hermes --resume <id>` against a terminal
(`agent_close`) session may spawn a NEW session id instead of continuing the
owner. Detect via state.db (new id, same model, prompt embedded, old id still
terminal). Record the lineage explicitly in the registry; the rule that
matters is single active writer, not id continuity. Never dispatch a second
correction session on top.
