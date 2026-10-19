# S10-C2 — T01C-C4 Meta-max continuation (verified 2026-08-29 00:34–00:48)

Continuation of `s10-c2-meta-max-same-model-routing.md` — same session
`20260828_180654_be71b5`, worktree `s08-integration`, after T02-C2 DONE.

## Why this exists
After T02-C2 proved 46/46×2 with the FULL id `ocg/deepseek-v4-flash` via
`custom` → `ocg` → opencode-go (23:06), user ordered (§1.4 mid-cycle
override, binding): "đổi worker sang model Meta-max giống bạn và chạy tiếp đi"
+ "bỏ hết các model khác khỏi luồng worker nhất là openrouter".
T01C-C4's previous dispatch (23:11, bare `deepseek-v4-flash` via any alias →
`cmc`/OpenRouter) had been killed EXIT=-15 at prefill (0 B log) — no
TASK/LOG/REPORT had landed yet, so the next resume is still the FIRST real
execution of that owner. The lesson is the **route switch on a live DAG
without losing the owner session**: same owner, same prompt file, new
provider+model pair, fresh log file.

## Verified 00:34–00:35 — probe matrix that decided the switch

Manager at that moment (29/08 00:34, `hermes config get`):

```
model.default: meta
provider: muse
base_url: http://127.0.0.1:20128/v1  (9Router)
providers.custom.model: ocg/deepseek-v4-flash
providers.muse.model:   ocg/muse-spark-1.2-contributor
providers.opencode.model: ocg/muse-spark-1.2-contributor
```

Probes (`HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`, `hermes -z "ping" --yolo`):

| Selector | Result | Meaning |
|---|---|---|
| (no flags) — default `meta`/`muse` | `pong ✅` | manager chat itself |
| `--provider custom -m meta` | `pong` | **Meta-max combo** — correct |
| `--provider custom -m ocg/muse-spark-1.2-contributor` | `HTTP 404: No active credentials for provider: opencode-go` | ocg-via-custom fails for Muse member (29/08) |
| `--provider muse -m ocg/muse-spark-1.2-contributor` | same 404 |  |
| `--provider opencode -m ocg/muse-spark-1.2-contributor` | same 404 | opencode-go has no active Muse credential at that moment |
| `-m meta` (no provider) | asks for prompt; with `-z "ping"` → pong via default? — ambiguous, never use bare |
| `--provider custom -m muse-spark-1.2-contributor` | `HTTP 404: No active credentials for provider: openai` | bare id resolves to `openai` alias |

Decision: worker route = exact manager-chat pair = **`--provider custom -m meta --yolo`**,
never the `ocg/muse-spark` long form, never a bare id, never `openrouter`/`cmc`.

## Dispatch that closed it

```bash
# registry before: USER MODEL OVERRIDE C2-v2: Meta-max giống manager (custom/meta)
sed -i 's|--provider [a-z]* -m [a-z/.-]*|--provider custom -m meta|g' \
  output/s10/c2/t01c-c4/prompt.txt output/s10/c2/t03-c2/prompt.txt \
  output/s10/c2/t04a-c2/prompt.txt output/s10/c2/t04b-c1-r1/prompt.txt output/s10/c2/t04c-c1/prompt.txt

HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes \
  --resume 20260828_003035_859fe5 \
  -z "$(cat output/s10/c2/t01c-c4/prompt.txt)" \
  --provider custom -m meta --yolo \
  >> output/s10/c2/t01c-c4/dispatch-meta.log 2>&1
```

- proc `71cac7d983fb` (00:30→00:44), hermes 27944 → python 30400, ESTABLISHED to 20128.
- Compression silence ~14 min (leaf CPU frozen 12.39 s, delta 90 s = 0) then burst.
- Log `dispatch-meta.log` 4 970 B, starts
  `RULES_LOADED path=.../HERMES_AUTOPILOT_RULES.md lines=180 sha256=987386c5…`
  (correct — unlike T02-C2 R4's bogus 37-line claim), preflight J1-v4 13/13.

## Evidence the worker left (and Manager independently re-verified)

Worker 00:44 log (Meta-max):

- `pytest tests/test_s10_full_apply_api.py tests/test_s10_full_apply_workflow.py -v -p no:cacheprovider --override-ini="addopts=" --basetemp fresh`:
  **23 passed run1 (~69 s) + 23 passed run2 (~69 s)** — 7 api + 16 workflow incl.
  7 negative (missing source/asset, fabricated mapping, unsupported route,
  zero chunks, stitch failure, caller crash-hook injection).
- `tests/test_s10_multi_role_apply.py -q : 46 passed` (T02 regression held).
- Ruff `--select F`: `All checks passed`.
- `git diff --check: 0`, `alembic heads: a10b11c12d3e` (worktree, not MAIN `d5e6f7…`),
  allowlist-only dirty set.

Manager J2 gate (00:47–00:48, fresh basetemp, `MOTIONFORGE_DATABASE_URL` UNSET,
`--override-ini="addopts=" --basetemp=…/s10c2-j2-run{1,2}`):

- **23 passed (74.15 s) + 23 passed (73.75 s)**, 0 failed/skip — J2 MANAGER_VERIFIED.
- Registry: `2026-08-29 00:47 +07 — J2 (C2) GATE MANAGER_VERIFIED — T01C-C4 DONE 23/23 x2 (Meta-max)`.
- Downstream T03-C2 dispatched 00:48 with same `custom/meta` pair
  (`proc_64f17996e2a5`, owner `20260828_011920_b79bd6`, `dispatch-meta.log`).

## Rules to carry

1. **Same-owner continuation across a user-ordered route change**: kill is by
   exact PID only; session context survives; reuse `prompt.txt` patched to
   the new pair, write to a new `dispatch-meta.log` (don't overwrite the
   killed 0 B log), record `USER MODEL OVERRIDE C2-vX: <provider>/<model>`
   with pong evidence in `S10-SESSION_REGISTRY.md`.
2. **Probe the EXACT pair before every resume** — a 0 B log after a resume
   is compression, not failure, for large owner sessions (session `003035`
   = hundreds of messages). Diagnose with two 60–90 s spaced probes
   (log-size delta + leaf CPU via `Get-Process`), not with a single 0 B
   check.
3. **User hard constraint "bỏ openrouter"** = no `openrouter`/`cmc`/bare-id/
   fallback on any later lane (T03/T04A/B/C) — patch all remaining
   `output/s10/c2/*/prompt.txt` in the same turn the override lands.
