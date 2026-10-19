# Required-reading death pivot + evidence traps (DV3-R2 T03, 2026-09-08)

Class lessons from a worker task that died 6 consecutive times (R1→R6) at
44–149 msgs with ZERO code artifacts — every death landed inside the
required-reading absorption phase (prompt ~5 KB + 6 required docs), never in
implementation. Applies to any manager dispatching long-prompt workers.

## 1. Pivot after 2 same-shape failures, not 6 identical retries

Retrying the identical full prompt after each death produced the identical
failure shape (death during reading, no bytes landed). Discipline already says
"same approach fails twice → switch approaches entirely" — enforce it here:

- After the 2nd identical-shape death, SPLIT the prompt: half 1 = write the
  module only (+ its own REPORT), half 2 = tests + evidence on the landed
  module. Each half carries a trimmed required-reading list (only what that
  half needs) instead of the full 6-doc packet.
- Record each attempt's death signature (msg count, last assistant line,
  artifacts landed: none/some) in commands.jsonl so the pivot decision is
  evidence-based, not impatience.

## 2. BGR-vs-RGB overlay measurement trap

`mask_overlay` drew `(255,0,0)` in **BGR** order = BLUE channel in RGB.
Measuring R-channel gain found 0.01% ("no mask"); measuring the correct
B-channel found 2.39% with a tight reader-only bbox (x221–328/y96–271),
overlap with protected-union 0.03%, outside-removal mean 5.3.
Rule: read the overlay code's channel order BEFORE measuring any tinted
review sheet — a near-zero measurement is a suspect, not a finding, until
channel order is confirmed.

## 3. Vision prose is not file evidence

A disputed word ("standing") existed only in a prior vision-model analysis
paragraph, in zero files. The worker correctly proved it with grep (zero hits
outside a test that bans the word). Rule: grep the files for the disputed
string before asserting it exists; never promote vision prose into a finding.

## 4. Resume may spawn a new session — record lineage honestly

`hermes --resume <id>` twice created a NEW session instead of continuing the
owner (verified via state.db: new id, prompt embedded, old session terminal).
Single-writer still held (old session terminal, no concurrent edit), but the
registry must record the true lineage (R1→R2→… with ids + evidence), never a
retrospective "same session" claim.

## 5. Stale file-mtime watchdogs

A watchdog keyed on REPORT.md mtime fired on an already-processed REPORT
(its mtime was newer than the correction prompt, but the content was the
already-verified R2 submission). Rule: on fire, compare against the
last-processed marker first; if stale, log END/STALE in commands.jsonl and
move on — do not re-verify or re-dispatch.

## 6. Manager reporting norm (this user)

Vietnamese; lead with status; ETA as a table with date anchors and explicit
buffers; instant notify on worker EXIT/blocker in the same turn; heartbeat
≤20 min during active runs. A question like "bao giờ xong" always gets a
fresh disk-truth check first, never a cached ETA.

## 7. Pixel-diff before vision on visual claims

For worker claims about frame events (book open/closed, pose changes),
self-extract the claimed frames and diff ROIs numerically BEFORE any vision
call: mean abs diff + pct-changed per ROI. Concrete case: claimed book-open
at source 516 measured 515→516 byte-identical (mean 0.0); the true event at
521→522 jumped ~151 mean in the correct ROI while the worker's first ROI
stayed ~0.006. White-pixel share inside the ROI is a cheap second signal
(static spine-edge 0.134% identical across 515/516/522 = no pages). Vision
then confirms on full frames, never on worker-supplied strips alone — one
5.3K worker strip showed curtain+wall, no book at all.

## 8. Window-vs-clip index mapping + transposed model tokens

- Record local↔source mapping explicitly (here output-local 0/60/119 =
  source 450/510/569). Probes extracted at clip 0/60/119 are NOT evidence
  for a 450..569 window — the manager made exactly this error, deleted the
  files, and recorded the correction in the decision-ack file.
- Transposed-token model IDs can BOTH pong (`...-1.3-contributor-free` vs
  `...-contributor-1.3-free`) while state.db proves worker and manager ran
  different strings. A pong is not alias proof: pin the exact string per
  task, verify via state.db/launch logs, and record errata without
  rewriting history (MODEL_ERRATA pattern: correct forward, preserve
  original text).
