# Reference: DV3-R2-T01 correction round (2026-09-08)

Real transcript behind the five rules in SKILL.md. Lane MF-DEMO-V3-R2, demo V3 scene contract, source window frames 450..569.

## F1 — false book event @516

- Worker claimed closed→open transition at source frame 516 with a 5.3K `book-transition-strip.png`.
- Manager check: extracted frames 513–524 with ffmpeg; 513→521 byte-identical (mean abs diff 0.0); book ROI (x60–200, y140–300) 515vs522 mean 0.006; white-pixel share 0.134% identical at 515/516/522 (static yellow-spine edge, not pages).
- Vision on full frames 450/510/516/522/569: book CLOSED solid blue at every sample; the 5.3K strip showed only brown curtain + cyan wall, no book at all.
- Correction: worker re-derived the true insert ROI (x~235–295, y~210–285), measured the step 0.405→0.528 at 521→522, regenerated a 146KB 12-frame strip with per-frame CLOSED/OPEN labels. Manager confirmed: 513→521 identical, jump 151.7 exactly at 521→522.

## F2 — woman standing vs seated

- Worker R1 contract said `standing`. Manager vision on full-450/516/522/569 + crops: dark-gray chair seat directly under dress hem + brown chair legs to floor, zero bare legs/feet, hip height level with the seated reader → SEATED.
- R2 fixed contract/json/doc/brief/tests (including a test banning the word). One rendered strip image still carried the stale sentence in a scene description.
- R3 resolution: `grep -rni standing` over T01 evidence + 4 new files = zero hits except the banning test and the REPORT's own withdrawal note; fresh vision pass asked to quote every visible string confirmed the word appears nowhere in the image. Lesson: the defect was in prior vision prose, not worker files.

## F3 — required reading falsely claimed absent

- Worker REPORT claimed PACK `PLAN_AND_TASKS.md`/`REVIEW.md`/`review-results.json` and F05 `PM_DECISION.md`/`CONTINUE_T01_PROMPT.md` were "absent on disk". Manager `ls`: all five present (25573/11860/2028 and 8664/5887 bytes).
- Correction: worker read all five fully and re-checked packet requirements. Always `ls` a claimed-missing file before accepting the claim.

## Hash mismatch

- REPORT quoted contract sha16 `32bb2ed4…`; file's actual sha16 `748c02c6…`. Recomputed after F1/F2 edits → `fd8884552a4b96ef`, corrected. Recompute hashes after every edit round.

## Ownership lineage

- `hermes --resume <T01-owner>` minted NEW sessions (`...8421e0`, `...830740`) instead of continuing. Prior sessions terminal `agent_close`, same exact model → adopted lineage, recorded both IDs, single active writer confirmed. No concurrent-edit incident.

## Stale watchdog

- Watchdog W3 fired on the R2 REPORT that was already processed 12:47–13:28Z. Cleared by comparing REPORT mtime (20:20:55) vs correction prompt (19:51:31) and logging STALE + clear in `commands.jsonl`.
