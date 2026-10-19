# S12-C2 re-kickoff after a partial first kickoff (2026-09-09 ~22:2x +07)

The user re-sent the same S12-C2 prompt ~2.5h after a first kickoff already
created the fresh evidence root. Sequence that worked:

## 1. Never create a second root — reuse the existing one

Before `mkdir`-ing a new `<run-id>-C2`, list the evidence dir:
`ls -la MotionForge2D-evidence/s12/*C2*` — a prior kickoff may already hold
`STATE_RECONCILIATION.md`, `MODEL_SWITCH.md`, `<lane>/prompt.md` and even a
`dispatch-*.log`. Read STATE_RECONCILIATION (records manager identity, model
policy + raw 429 evidence, watcher kill proof, owner table) and the lane
dispatch log TAIL before doing anything — the previous W1 dispatch outcome is
in that file, not in chat history.

## 2. Dispatch log may end in a transport error AFTER an analysis-only turn

`dispatch-1` (19:52) resumed the exact T01 owner; the log shows the worker
only READ (RULES_LOADED → review → findings analysis, no code) then the
wrapper died with:
`API call failed after 3 retries: HTTP 503: [opencode-go/deepseek-v4-flash] [502]: fetch connect timeout (reset after 10s)`
That is an analysis-only turn + transient 502 → the lane is at zero state
advance and needs a retry, NOT a status nudge and NOT a new worker.

## 3. Route probe needs the REAL key from config — never a redacted one

`curl` with the display-redacted key (`Bearer sk-cff…`) returns
`{"error":{"message":"Invalid API key",...,"code":"invalid_api_key"}}` — a
FALSE auth blocker; the probe itself was malformed. Read the live key from
`C:/Users/Admin/.hermes/config.yaml` (regex the `custom:` provider block's
`api_key:` line, `utf-8-sig`) and probe via python urllib POST
`http://127.0.0.1:20128/v1/chat/completions` with `max_tokens:5`.
`PROBE_OK 200` = route live → re-dispatch same session/model.
Wall-clock already satisfied the ≥5-min wait (19:52 → 22:2x), no extra sleep.

## 4. Complete W0 evidence during the retry turn

The first kickoff had STATE_RECONCILIATION + MODEL_SWITCH but no MATRIX /
SESSION_REGISTRY. While the retried W1 runs in background, write:
- `MATRIX.md` — all 32 rows with C2 Fxx/Mxx focus + the F01–F11 grouped-defect
  mapping copied from RECHECK.md (create timestamp in the header);
- `SESSION_REGISTRY.md` — owner table incl. frozen/stopped duplicates,
  model policy, DAG.
Then report RULES_LOADED (path + SHA + lines, read fully THIS turn), canonical
local==remote, watcher-free, W1-running.

## 5. Truncated pre-kickoff artifacts ≠ live state

If the prior kickoff's artifacts reference model/owner facts that changed
(MODEL_SWITCH says ocg/deepseek-v4-flash because CMC weekly 429 resets
2026-09-11T17:23Z), re-verify against the live registry before dispatching —
the re-sent prompt's CMC pin is superseded by the recorded user override;
dispatch on the recorded override and keep both facts in the packet.
