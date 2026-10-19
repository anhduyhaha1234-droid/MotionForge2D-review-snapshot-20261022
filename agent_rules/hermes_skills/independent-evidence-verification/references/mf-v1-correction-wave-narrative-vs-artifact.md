# MF-RESKIN correction wave — narrative vs artifact, report-only reclassification, freeze protocol

Run id `20260922T0955Z`. Three owner corrections dispatched after an independent review of packet
`20260922T0345Z` returned `CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED` with rows F01–F11.

## 1. The contradiction (why §27 exists)

| Place | Verdict it carried |
|---|---|
| Lane's final chat response | `SHUTDOWN_CONFIRMED` (with a prose explanation that PID 21092 was "my own `w2_run_stage.py`") |
| `VIDEO14B/wave2/SHUTDOWN.md` (same mtime as the report, 13:37:43) | `verdict: SHUTDOWN_UNPROVEN` + `COLLATERAL (removed but not in the engine chain): [21092] -> COLLATERAL DAMAGE — INCIDENT` |
| `wave2_shutdown_evidence.json` | same conflict, plus `collateral_removed: [21092]` |

Two incompatible verdicts in one evidence set. Manager response: measure the physical end state
first, then force a report-only reclassification.

### Physical state the Manager measured independently
- port 8210 `connect_ex` = **10061** (`WSAECONNREFUSED`), no LISTENING row
- VRAM **597 MiB** idle of 12,227
- `hermes desktop` 14872 + `hermes serve` 29648 **still alive**; full `python.exe` set = exactly those two

Conclusion available immediately: the engine was genuinely down. Only the *classification* of one PID
was open — a much narrower question than the verdict string suggested.

### The datum that resolved it, from the lane's own file
- `python_pids_before` contained `21092`; `listeners_before` contained
  `TCP 127.0.0.1:64381 127.0.0.1:8210 ESTABLISHED 21092` — i.e. 21092 was a **client of the engine**
- the before-dump's cmdline for 21092 was
  `python.exe -u experiments/mf_reskin_v1/video14b/tools/w2_run_stage.py …/mf_animate2_book4s.api.v6.json animate2_book4s_1A_r5 … --timeout 1200`
- `stop_log` targets were exactly `[31024, 31452]` — 21092 was never targeted
- its own run record showed it exited on `ConnectionRefusedError 10061` when the engine died

## 2. The report-only reclassification the correction round had to produce

Allowed to change ONLY these fields:
`collateral_removed`, `collateral_removed_first_pass_raw`, `pid_classification`, `verdict`,
`previous_verdict_first_pass`, `correction_round`, `report_only_reclassification`, `superseded_first_pass`.

Required restraint proof embedded in the artifact:
`engine_started: false`, `model_loaded: false`, `pid_stopped_by_this_tool: false`,
`media_bytes_changed: false`, `metrics_remeasured: false`, plus `changed_fields_only: [...]`.

Result:
```
verdict: SHUTDOWN_CONFIRMED_WITH_DISCLOSED_OWN_CLIENT_EXIT
collateral_removed: []            collateral_removed_first_pass_raw: [21092]
pid_classification.21092.class: own_client_process_exited_after_engine_stop
```

Superseded block kept inside `SHUTDOWN.md` verbatim:
```
## SUPERSEDED first-pass verdict (kept verbatim, not deleted)
- verdict: SHUTDOWN_UNPROVEN
- why superseded: the first pass computed COLLATERAL as (removed - engine_chain) with no ownership
  test, so the own stage runner 21092 … was mis-attributed to the stop action.
```

Manager verification of the correction:
- verdict token grep across `SHUTDOWN.md` / `wave2_shutdown_evidence.json` /
  `wave2_shutdown_classification.json` / `WAVE2_REPORT.md`: new string present everywhere, old string
  only inside the superseded block
- media re-hashed: `final_vace14b_book4s_4s.mp4` `ca42806b…` and `raw_vace14b_book4s_121f.mp4`
  `0630c87d…` **unchanged**
- ports re-probed: 8210 and 8199 both 10061

## 3. The 15 adversarial classifier cases (the part that makes the verdict trustworthy)

```
own client + engine-client row            -> CONFIRMED_WITH_DISCLOSED_OWN_CLIENT_EXIT, collateral []   PASS
foreign pid lost (not own, not engine)    -> UNPROVEN, collateral [9999]                 <- no false CONFIRMED
own-tool cmdline but no client row        -> UNPROVEN, collateral [21092]                <- no inference
chain pid without taskkill rc=0           -> UNPROVEN (basis false)                      <- no upgrade
port still open (connect_ex_after 0)      -> UNPROVEN
LISTENING row still present after stop    -> UNPROVEN
```
Harness + fixture were written under `%TEMP%` and deleted, because the packet's write-set was
"tools only" — a lane that declines to grow the repo to test itself is behaving correctly.

## 4. Three claims the review disproved — in the MANAGER's own packet

| Old claim (manager packet) | Reviewer evidence | Replacement |
|---|---|---|
| "raw PTS is impossible to satisfy" | `media-probes.json`: raw 121 frames are already **CFR 30 fps, presentation PTS 0…61440 step 512** | the packet author read B-frame **decode-order** packet PTS and mislabelled it; a re-encode of the *presentation* stream is unnecessary |
| "export drops the padding" | `raw-to-export-pixel-map.json`: output 0…118 ↔ raw 0…118, **output 119 ↔ raw 120** | raw 119 was dropped and the padding frame kept — the opposite of the claim |
| "640×368 is the expected geometry" | source window is 640×360 | 640×368 was produced by **stretching** 360→368; correct handling is pad (same transform for source/reference/control) then crop back to 640×360 |

Handling: the owning lane must emit `CLAIM_CORRECTIONS.md`; the disproof goes into the next packet's
required reading; the manager marks the wrong claim as its own in the wave report.

## 5. Freeze protocol (replaces last wave's shared live evidence root)

Last wave BENCH evaluated while VIDEO14B was still writing siblings in `NEW_EV/VIDEO14B/**` (9 files
touched 13:49–13:56 during the evaluator's run). BENCH flagged it itself and was safe only because the
clip was already frozen (`ca42806b…`, mtime 13:25:24, unchanged).

This wave's protocol: **owner terminal → manager byte-snapshot the whole subtree (media + run record +
graph + frame-map + pins) into `manager/frozen/<candidateID>/` with a hash manifest → evaluator reads
only that frozen copy**. A correction means a new candidate ID and a new freeze; never reuse a path and
mutate files a review has already read.

## 6. Guard manifests captured before dispatch (three disjoint write-sets)

| Set | Count | Source | Snapshot |
|---|---|---|---|
| protected-only | 40 (MAIN canonical docs, source film/audio, OLD packet+media+reports, READ review evidence, GOLDEN fixture) | explicit list | pre-dispatch verify **VERIFIED, 0 failures** |
| COMFY write-set | 22 tracked, 0 dirty, 230,640 B | repo-relative walk of `experiments/mf_reskin_v1/comfy` | 22/22 hash-match |
| VIDEO14B write-set | **61 untracked**, 952,368 B | worktree experiments + runtime video14b tools/logs/json (weights excluded — hash-pinned in `DOWNLOAD_MANIFEST.json`) | 61/61 hash-match |
| BENCH write-set | 13 tracked, 133,061 B | repo-relative walk of `experiments/mf_reskin_v1/bench` | 13/13 hash-match |

Protected and task write-sets are kept **disjoint** (§8's manifest-composition rule) so a live lane's
own edits cannot fire `protected_file_changed`.
