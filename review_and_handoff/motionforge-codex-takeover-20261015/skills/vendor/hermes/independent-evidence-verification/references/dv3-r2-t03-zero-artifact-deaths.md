# DV3-R2-T03 zero-artifact death loop (session evidence, 2026-09-08/09)

Task DV3-R2-T03 (pose_composition.py + test_r2_pose_composition.py) died FOUR
times with zero artifacts. Manager: 20260908_165201_c0780f. All workers on
exact `cmc/meta/muse-spark-1.3-contributor`, max, fallback OFF.

## Death table (all verified against disk truth, not log text)

| Attempt | Owner session | End (UTC) | Msgs | Last assistant msg | Artifacts |
|---|---|---|---|---|---|
| R1 | 20260909_001512_641954 | 17:24:22 | 149 | "Continuing —" (12 chars) | none; runtime T03/ dirs empty |
| R2 | 20260909_031828_70e01f | 20:24:35 | 70 | "TARGET checklist" (16 chars) | none |
| R3 | 20260909_032547_7042f4 | ~20:32 | 68 | "Baseline complete — moving to implementation." (45 chars) | none |
| R4 | 20260909_033328_05217c | ~20:40 | 73 | "Required reading done + existing T03 attempts before writing." (61 chars) | none |
| R5 | 20260909_034112_b44f40 | live @20:42 | — | dispatched, watchdog W10 armed | pending |

Wrapper EXIT was 0 every time (bash wrapper exit ≠ worker verdict).
Dispatch logs held only the EXIT line (0–746 bytes).

## Death signature (all four)

- Last assistant message <100 chars, always a preflight platitude.
- Message count 65–150 (a working session in this lane runs 150+).
- BOTH allowlisted new files absent; owned runtime T03/{output,projects} empty.
- Session `end_reason=agent_close` (infrastructure/connection class, not a verdict).

## Guards re-run before every resume (all VERIFIED/unchanged each time)

- `T03/t03-prewrite-manifest.json`: VERIFIED 11/11 (proves the dead worker wrote nothing).
- MAIN DB `e94184a3…705`, 1011712 B — unchanged.
- Demo HEAD `1f5936d`, S12 `0d2e063a` clean, T01 contract hash16 `63be9c4ddc87e42d`.

## Resume lineage (runtime minted NEW sessions on --resume)

R1 `...641954` → R2 `...70e01f` → R3 `...7042f4` → R4 `...05217c` → R5
`...b44f40`. Adopted in registry; single active writer confirmed
(all priors terminal `agent_close`).

## Watchdog record

- W6 (180min on T03/REPORT.md): TIMEOUT exit 2 at 20:17:12Z — correct, no REPORT existed.
- W7/W8/W9/W10 re-armed per attempt; W4 (T02) TIMEOUT exit 2 then W5 fired on-time (marker after 120 min) — timeout-then-fire is the normal pattern, not an error.

## Lesson encoded as SKILL.md §7

After two consecutive zero-artifact deaths, shrink the resume payload
(micro-prompt: 2 missing files + 5 must-run tests + env block) instead of
re-sending the full ~15-doc required-reading packet; split the task if a
third attempt also dies in reading.
