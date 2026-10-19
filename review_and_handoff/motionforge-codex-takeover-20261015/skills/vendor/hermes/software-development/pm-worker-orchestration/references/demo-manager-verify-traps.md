# Demo-lane manager verify traps (DV3-R2 T03/T04, 2026-09-08/09)

Manager-level lessons from a lane where workers repeatedly died before writing code, plus verification traps hit while gating their output. All verified live this session.

## 1. Lean-split pivot after repeated reading-phase deaths

Signal: 3+ consecutive worker deaths with ZERO artifacts, deaths at low message counts (44–73 msgs), last messages stuck in required-reading phase. The full prompt (~5KB + 6 required docs) kills the worker before it writes a byte.

Fix (worked: T03 stepA landed a 550-line module, stepB 6 tests green): split the task into two lean prompts —
- stepA: module only, ~2KB, facts INLINED (frozen truth bullets), no heavy reading list, no tests/docs/REPORT;
- stepB: tests + stills + REPORT, reads stepA's module + note.
Record the pivot + reason in commands.jsonl; per discipline rules, same approach failing 3x means pivot, not retry.

## 2. Resume-lineage check (hermes --resume may fork)

`hermes --resume <owner>` sometimes creates a NEW session instead of continuing the owner. After EVERY resume dispatch, query state.db for the newest session: check its first user message contains your prompt and its model matches, then record lineage (R1→R2→R3) in the registry. Never assume the owner continued.

## 3. Stale-watchdog conditions

A watchdog firing on `REPORT.md newer than prompt-file` re-fires on an already-processed report (m differential, same content). Conditions must compare against the manager's last-PROCESSED marker (gate timestamp recorded in commands.jsonl), not the prompt mtime. On a stale fire, log an END/STALE entry with the reason and clear it — don't re-verify.

## 4. Untracked guard-manifest false positive

`write_set_guard.py verify` reports `protected_file_changed` for UNTRACKED files whose bytes differ from capture. If the flagged files are pre-existing untracked pilot bytes (not worker edits), confirm with `git status --porcelain` (shows `??`) + `git diff --stat` (tracked-only, shows only pre-existing dirt) before freezing the writer. Record the false-positive analysis; don't waive real drift.

## 5. Overlay channel-order measurement trap

Mask-overlay code may convert BGR→RGB (`...[:, ::-1]`) BEFORE tinting, so the "red" removal tint lands in the PNG's BLUE channel. Measuring red first reads ~0% and looks like a missing mask. Always read the overlay code's channel order first, then measure the matching channel; cross-check the changed bbox against expected anatomy (here: x221–328/y96–271 = reader chest, overlap with protected-union 0.03%).

## 6. Vision fallback ladder for local images

When `vision_analyze` returns omitted/connection-error on local paths: (a) split composite sheets into per-cell PNGs and retry; (b) if still blind, measure programmatically (PIL channel-diff + bbox + overlap + inside/outside means). Pixel stats plus code reading closed every visual gate this session without a single successful image view.
