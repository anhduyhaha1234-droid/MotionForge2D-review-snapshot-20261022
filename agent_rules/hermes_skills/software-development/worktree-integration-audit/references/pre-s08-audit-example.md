# Pre-S08 Audit — worked example (MotionForge2D, 2026-08-05)

Concrete evidence from the first real run of this audit. Reuse the shapes,
not the exact numbers.

## Tree status snapshot

```
MAIN (C:/Users/Admin/MotionForge2D, master @ a43b20d): 45 entries = 29 M + 16 ??
S05 (prepare-s05-t01, codex/prepare-s05-t01 @ a43b20d):  55 entries = 9 M + 46 ??
S06 (s06-t01-review, codex/review-s06-t01 @ a43b20d):    45 entries = 14 M + 4 A + 8 AM + 2 MM + 17 ??
S06-old (s06-t01, codex/s06-t01 @ 1a3e0fd):               5 M   # HEAD differs → not authoritative
```
All trees dirty; HEAD alone proves nothing (S05/S06 share HEAD a43b20d with
MAIN yet carry the entire sprint as uncommitted work).

## Delta / overlap outcome

- 5 overlapping paths: app/api/app.py, app/api/deps.py, docs/pm/ROADMAP.md,
  frontend/src/lib/api.ts, frontend/test-results/.last-run.json
- 3 REAL conflicts by hunk count: app.py (9 hunks), deps.py (12), api.ts (12)
- ROADMAP = trivial status-line conflict; .last-run.json = do-not-merge artifact

## MAIN incident comparison (agent once wrote into MAIN by mistake)

| MAIN file | vs S06 review tree | meaning |
|---|---|---|
| app/api/app.py | GIONG (identical) | MAIN already carries S06 content |
| app/api/deps.py | KHAC 16 lines | stale copy |
| app/api/routes/durable_characters.py | KHAC 180 lines | stale copy |
| frontend/src/app/(app)/characters/page.tsx | KHAC 1371 lines | stale copy |
| tests/test_pack_publish_ux.py | only in MAIN | quarantined in review tree |

Never clean these up in the audit — flag for the authority.

## Baseline evidence check

```bash
python -c "import json; d=json.load(open('<tree>/output/quality-baseline/<RUN>/summary.json')); print(d.get('overall'))"
# → {'status': 'PASS', 'exit_code': 0}
grep -E "Decision|Run ID" <tree>/docs/pm/sessions/<TASK>/PM_REVIEW.md
stat -c "%y" <tree>/docs/pm/sessions/<TASK>/REPORT.md
```
Found inconsistency: s06 ROADMAP row still `S06-T05 = SUBMITTED` while
PM_REVIEW says APPROVED; MAIN ROADMAP rows still PLANNED for S05/S06.

## Report section titles that worked

1. Tree / Branch / HEAD / Status table
2. Process table
3. S05/S06 authoritative-source table
4. Overlapping files / conflict table
5. MAIN incident comparison
6. Integrated-base options
7. Protocol changes required (quote exact lines)
8. S08 dependency confirmation
9. Blockers needing Codex/user authority
10. Recommendation

## Integrated-base options (proposed, not executed)

- Option A: S05 tree as base, apply S06 delta (35 paths) → preferred (most
  recent Codex review, newest baseline)
- Option B: S06 tree as base, apply S05 delta (45 paths)
- Both require manual 3-file merge (app.py, deps.py, api.ts) + ROADMAP, then
  fresh 7/7 baseline + full pytest + tsc/eslint + Playwright smoke.
