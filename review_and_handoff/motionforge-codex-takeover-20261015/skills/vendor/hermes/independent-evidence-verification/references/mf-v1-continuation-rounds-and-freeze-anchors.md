# MF-RESKIN-V1 continuation rounds — freeze anchors, accepted FAILs, a detached child

Worked example behind `independent-evidence-verification` §19. Same wave as
`mf-v1-golden-iteration-cap-and-acceptance.md` (round 1 of the GOLDEN lane) and
`mf-v1-comfy-readonly-release-and-pins.md` (the COMFY lane); this file covers the
**round-2/3 adjudication** that followed.

## 1. The correction that asked permission first (GOLDEN, round 3)

The lane ended round 2 by listing three decisions for the Manager. Decision #2 was a
real defect it had found in its own output and deliberately not fixed:

- **Defect:** reference cutouts were clipped by the *annotation's declared bbox* rather
  than the mask's tight bbox.
- **Measured:** `verdict_histogram {"CLIPPED": 88}`, mask px outside declared crop
  **9,058 / 2,089,631 = 0.433474 %**, worst single role **990 px (0.467 %)**.
- **Why it mattered:** the next task diffs role-by-role against exactly these cutouts, so
  a systematic crop error would enter the baseline of every downstream comparison.
- **Why it had not been fixed:** the fix required rewriting a round-1 tool file, and the
  Manager's own packet had said round-1 bytes must stay byte-identical. It asked.

Authorised as a bounded correction with three conditions: fix the crop to the mask's
tight bbox; re-assert that the **fixture and keyframes stay byte-identical**; and if the
residual cannot reach 0, report the residual with the measured reason rather than
redefining the check.

### Result (Manager-verified on disk)

| Metric | Before | After |
|---|---|---|
| verdict histogram | `{"CLIPPED": 88}` | `{"EXACT": 88}` |
| mask px outside crop | 9,058 | **0** |
| loss % of mask px | 0.433474 | **0.0** |

The artifact keeps **both** generations of the number — `mask_px_outside_crop: 0`
alongside the historical `mask_px_outside_declared_crop: 9058` and
`loss_pct_of_mask_px_declared: 0.433474` — so the superseded measurement stays auditable.

### Freeze anchors re-asserted (this is the actual verification)

| Anchor | Value | Verdict |
|---|---|---|
| `GOLDEN_FIXTURE.json` sha256 | `7e1627e4…cd0dab` | **byte-identical** to round 2 |
| `freeze_hash_sha256` | `2c558ce1…fa684` | **unchanged** |
| commits | `4768be0` → `dcf0544` → `3093415` → `61dff8d` | allowlist only, `remotes = 0` |

A 0 px result with a moved fixture hash would have been a re-freeze, not a fix. Check the
anchors **before** admiring the metric.

## 2. The accepted FAILs (PROPAGATE, round 1)

Four of seven windows measured before the lane died. Reading these numbers out of its own
sweep log (not its prose) is what let round 2 be scoped to the remainder only:

| Window | frames | mae_mean | psnr_med | conf | resets | contact | continuity | peak_rss | wall |
|---|---|---|---|---|---|---|---|---|---|
| BOOK | 120 | 0.277887 | 37.7243 | 0.870147 | 0 | **PASS** | PASS | 1038.27 MiB | 70.384 s |
| CUT_660 | 120 | 9.127326 | 36.6088 | 0.816202 | **2** | FAIL | PASS | 1038.74 MiB | 59.94 s |
| TURN_795 | 120 | 8.54389 | **16.2013** | 0.772308 | 0 | FAIL | PASS | 1035.29 MiB | 59.725 s |
| CAM_4212 | 120 | 3.166199 | 30.2427 | 0.790485 | **1** | FAIL | PASS | 1038.30 MiB | 66.689 s |

Three things these establish, none of which needed a visual verdict:

- **Bounded memory on real content** — peak RSS ≈ 1,035–1,039 MiB per 120-frame window,
  against a ≤16 GiB streaming target. That is the measured answer to the "decode the whole
  film into RAM" finding (whole-film RGB at 1080p/30 min would be ~313 GiB).
- **Reset events fire on real discontinuities** — non-zero exactly where the source has a
  cut or new view (CUT_660 = 2, CAM_4212 = 1) and zero where it does not (BOOK, TURN_795).
  A hard reset that never fires is indistinguishable from no reset.
- **The two negatives are genuinely independent** — `contact=FAIL` while `continuity=PASS`
  on the *same* windows. That is positive evidence for the acceptance row demanding the
  two be separately failable, and it is exactly what the previous generation of the demo
  chain failed (a contact failure waived by a revision string).

Kept as measured, not tuned away: `contact=FAIL` on 3 of 4 windows, and
`TURN_795 psnr_med 16.20` sitting badly below 36–38 elsewhere. The route was at its
adjustment cap, the gate had been pre-registered, and the correct move was to escalate the
**route** decision with these numbers rather than dispatch more tuning.

## 3. The detached child that died with its lane

The lane launched its own 7-window sweep as a background process, reported the PID and log
path, and ended its turn at the iteration cap. Its stated plan — "when the sweep finishes,
run assemble → report → acceptance → commit" — could never execute: **the child died with
the worker**, frozen part-way through the 5th window.

### Detection (what actually worked)

A single recent-mtime count **lied**: `find <runtime> -type f -newermt "-4 minutes" | wc -l`
returned **183**, because those files had been written moments before the child died and the
window was still catching them. It looked like an active writer.

The two-point sample was decisive:

```
A=$(find "$R" -type f | wc -l);  L1=$(wc -c < "$R/sweep.log")   # 487 / 2959
sleep 45
B=$(find "$R" -type f | wc -l);  L2=$(wc -c < "$R/sweep.log")   # 487 / 2959  → STALLED
```

Both counters flat across 45 s, plus zero matching processes, plus the completed-window
count in the log (`grep -oE "\[full\] [A-Z_0-9]+: frames" | sort -u` → 4 of 7) = dead, and
precisely how much remained.

### Recovery

Resumed the **same** owner session with a finishing-only packet: the four completed windows
named as accepted with "do not re-run these", the three remaining windows, the assembled
set, the report/acceptance/guard/commit steps, and an explicit instruction to run the
remainder **synchronously** because a detached child is what killed the previous round.

## 4. Two independent lanes converged on the same blocker

The strongest signal in the wave came from two lanes that never communicated:

- **PROPAGATE:** *"the held keyframes are source-derived … so this is a propagation-mechanism
  proof, not a reskin"* — its low `BOOK mae 0.278` reflects faithful reproduction of the
  source, not an appearance change, because the new-identity artwork does not exist.
- **COMFY:** at every denoise that preserved geometry (template-match shift **0.0 px**), the
  appearance change was **LUT-explainable** (edge IoU 0.388 → 0.927 under a fitted
  per-channel map; 92.7 % of masked pixels within ≤16/255); raising denoise escaped the LUT
  (0.677) but destroyed structure (0.445 at 1/8 scale).

Two lanes, independent methods, same conclusion: the **mechanism chain is proven, the
appearance transformation is not**, and on the img2img route the two requirements move in
opposite directions. When independent lanes converge, treat it as the wave's finding and
escalate the open decision (which engine route) instead of scheduling more attempts on the
same route.
