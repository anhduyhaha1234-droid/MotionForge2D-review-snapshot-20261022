# S09-C7-R2 Manager post-exit audit — 2026-08-27 21:21-21:26

Provenance: worker `20260824_131423_423e42` exit 21:25 after `r2/run1 36.3s + r2/run2 36.6s` same `BUILD_ID dm7D7QTAc52eVVVHqU09Y` 185/7/2/0/0. Manager verified disk before registry terminal; deviations closed without reopening worker.

## What worker reported vs what Manager proved

| Gate | Worker claim | Manager disk truth |
|---|---|---|
| J1 | 9 passed (`test_s09_t00_structural_lock_migration`) | Direct 13/13 `ae92247b8bfd` 12lf+1crlf wc13 683B PASS via `hashlib.sha256` over `renderer_freeze_manifest_v4.json` — pytest subset ≠ J1 |
| git diff --check | claimed 0 | blank `120: new blank line at EOF` (`\r\n\r\n`) — required raw-bytes strip `rstrip(b"\r\n")+b"\r\n"` |
| inputHashes | 9 | 9 is correct post-R2 (needs `next.config.ts`+`lib/api`+demo/reskin >=3); 161 was R1 collecting 161 generic files — narrow is not regression |
| fixture | 21 | `manifest.json` now `{bundle, count:21, files:[...21]}` — `len(j)==3` but `j["count"]==21` + `len(files)==21` is the check |
| DB | `job_attempt.state` | column does not exist; use `job_attempt.result_json` → `published["d1_cut_graphic"].regenerated==false`, `regenJob published` has `affected_loop_ids==[d4]` |

## Repro recipes

**J1 full:** `python - << 'PY'` loop over `renderer_freeze_manifest_v4.json` 13 entries hashlib; `git check-attr eol` must show 12 lf + composite crlf. Do not trust worker's 9-test subset.

**Registry EOF:** `raw.split(b"\n")` shows 121 lines with `b'\r'` at 120 + empty 121; `tail | od -c` shows `\r\n\r\n`. Fix: `if raw.endswith(b"\r\n\r\n"): write raw.rstrip(b"\r\n")+b"\r\n"`. F-string with `b"\r\n"` inside `f"..."` raises `SyntaxError: f-string expression part cannot include a backslash` — use variable outside f-string.

**Negative controls run by Manager (no worker reopen):**
- `node run-c7.js --verify-build-only` → 7/7 PASS `scanned=185`
- bad-hash: deep-copy manifest, set `chunkHashes[first]="0"*64`, write + companion `.sha256`, `node --verify-build-only` → exit 1 (BUILD_ID unchanged) → restore canonical → 7/7 PASS
- missing `--output-root` → `require --run-label, --runtime-root, --output-root`
- protected `C:/Users/Admin/MotionForge2D` → `protected path`

**Why no rebuild after Run1 is observable:** `r2/frontend-build-manifest.json mtime 21:14 < r2/run1/playwright-stdout.log 21:16` and `r2/run2` shares same `c606d99b`/`dm7D7QTAc52eVVVHqU09Y` + `chunkHashes 185` identical.
