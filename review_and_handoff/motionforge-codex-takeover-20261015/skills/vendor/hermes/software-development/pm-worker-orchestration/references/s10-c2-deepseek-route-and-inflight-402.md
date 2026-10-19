# S10-C2 — DeepSeek route override + OpenRouter in-flight budget 402 (verified 2026-08-28)

Manager-side verified detail for the two dispatch lessons added to SKILL.md.
Correction cycle S10-C2, worktree `s08-integration`, model override
`deepseek-v4-flash` (effective `ocg/deepseek-v4-flash` via 9Router
`http://127.0.0.1:20128/v1`, reasoning max, fallback OFF, TTFB 900).

## 1. The selector alone is NOT a route — use the FULL model id (`ocg/` prefix)

CORRECTED 28/08 evening: the earlier "working" dispatch in this file used
`-m deepseek-v4-flash` (bare) and DID run prefill, but it routed through the
WRONG upstream — 9Router resolves the bare string via its `kv` table to
`providerAlias: cmc` → OpenRouter, whose balance is a separate exhausted
pool (`[openrouter/deepseek-v4-flash]` in the 402 body proves it). The user
correction ("dùng chính model tôi đang chat với bạn... bỏ openrouter") plus
9Router DB inspection showed the `ocg/`-prefixed id routes to opencode-go
connections that have never hit 402. RULE: worker model = the EXACT
provider+model pair the manager chat session runs, verbatim.

Persistent config (config.yaml) at dispatch time:

```yaml
model:
  default: meta
  provider: muse
  base_url: http://127.0.0.1:20128/v1
providers:
  custom:
    name: 9Router
    base_url: http://127.0.0.1:20128/v1
    model: ocg/deepseek-v4-flash   # <-- the full id IS the route key
    api_key: sk-cff...c38f
```

Failed probe (WRONG — no provider flag): `-m deepseek-v4-flash` alone →
`No usable credentials found for provider 'deepseek'` (token parsed as
provider name).

Working probe (RIGHT — full id + provider pair):

```
$ HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --provider custom -m ocg/deepseek-v4-flash -z "ping" --yolo
pong ✅
```

Dispatch command (VERIFIED — full model id, no 402 through opencode-go):

```
HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner_id> \
  -z "$(cat output/s10/c2/t02-c2/prompt.txt)" \
  --provider custom -m ocg/deepseek-v4-flash --yolo >> dispatch.log 2>&1
```

CAVEAT: a `ping` probe passing is NOT proof of route health for workers —
ping is ~200 tokens, worker prefill is 60–70k. A probe must approximate
worker prefill size (or simply resume and watch for the first log burst).

### Decisive diagnostic: 9Router routing truth lives in its SQLite DB

When a model 402s or routes ambiguously, INSPECT the router, don't guess:

```
C:\Users\Admin\AppData\Roaming\9router\db\data.sqlite
```

Tables: `kv` (model-id → providerAlias resolution), `providerConnections`
(upstreams, keys, priority, isActive), `providerNodes`, `combos` (combo
kind → model list), `usageHistory` (which provider actually served a model:
`SELECT model, provider, COUNT(*) FROM usageHistory GROUP BY model`),
`requestDetails`. Example decisive rows:

```
kv["deepseek-v4-flash"]            -> {"providerAlias":"cmc","id":"deepseek/deepseek-v4-flash"}  # OpenRouter-ish
kv["ocg|deepseek-v4-flash|llm"]    -> {"providerAlias":"ocg","id":"deepseek-v4-flash"}            # opencode-go
usageHistory: model=deepseek-v4-flash provider=opencode-go count=1945   # healthy upstream
```

An id that `usageHistory` shows thousands of successes on is the route to
pin; the alias in `kv` names the pool. All four Hermes providers
(custom/muse/opencode/ocpreview) share base_url + api_key, so only the MODEL
ID string decides the upstream — never assume an alternate provider alias
changes the credit pool.

## 2. OpenRouter in-flight budget 402 — the 3-attempt failure arc (19:03–20:52)

The Manager chat (this Hermes desktop session) itself ran
`ocg/deepseek-v4-flash` via the same 9Router/OpenRouter upstream. Every
Manager tool call = one in-flight request of ~200k tokens:

```
agent.log: API call #51: model=ocg/deepseek-v4-flash provider=custom
in=215822 out=215 total=216037 latency=8.9s cache=215552/215822
```

T02-C2 worker resume attempts under that contention:

| Attempt | Time | Observable | Verdict |
|---|---|---|---|
| R1 | 19:41 → 19:45 | 156-byte log, 1 line printed, EXIT=0 | early exit (402 already queued) |
| R1b | 19:46 → 20:24 | 0-byte log 37 min, leaf CPU +0.009s/min, ESTABLISHED socket to 20128 | diagnosed as stall → killed exact PIDs 29872+14152, EXIT=127, waited 5 min |
| R1c | 20:30 → 20:52 | 0-byte log, CPU creep +0.04–0.09s/min, then EXIT | raw 402 visible at exit |
| R1d | 20:59 → | no-poll policy started | running |
| R2 | 21:19 → 21:43 | `--provider opencode -m deepseek-v4-flash` (bare id, opencode alias) | 402 `Prompt tokens limit exceeded: 71410 > 60990` — provider alias alone does NOT change pool |
| R3 | 22:25 → 22:27 | same bare id via opencode; ping probe passed seconds before | 402 `64350 > 58353` — ping (~200 tok) passes while 64k prefill fails |
| R4 | 22:36 → 23:06 | `--provider custom -m ocg/deepseek-v4-flash` (FULL id) | **SUCCESS**: 46/46 ×2 PASS (26.24s/26.16s), J1 manager-verified, J1-v4 13/13, S09 renderer regressions 103/103 — fix proven end-to-end |

Raw error (dispatch-r1c.log tail):

```
Billing or credits exhausted: HTTP 402: [openrouter/deepseek-v4-flash] [402]:
{"error":{"message":"This request would exceed your available credits given
your current in-flight requests. Retry after in-flight requests settle, or add
credits.","code":402,"metadata":{"reason":"in_flight_budget_exhausted",
"limit_source":"openrouter_in_flight[...]
```

### Attribution rules (don't kill, don't replace)

- Distinguish from compression silence: compression = +0.05–0.65s/min CPU
  creep and eventually bursts tens of KB. In-flight contention can show
  slimmer creep (0.009–0.09s/min) and NEVER bursts — it dies at 402.
- Distinguish from true stall: true stall freezes AFTER visible progress;
  in-flight contention is a long initial silence that ends in 402 at exit.
- Decisive signal: check dispatch.log tail AFTER exit for `402
  in_flight_budget_exhausted`; check that Manager session shares the model.
- Never create a replacement session: Rules §7 recovery = wait 5 min, resume
  SAME owner, SAME prompt, SAME provider/model pair.

### No-poll policy (the fix)

Manager must NOT run `process wait` loops / repeated `tail dispatch.log`
while the worker runs — each poll is another in-flight request competing with
the worker's prefill. Dispatch → append registry → end turn. Rely on
`terminal(background=true, notify_on_complete=true)`; the notification wakes
the Manager when the worker exits. This is the operational consequence of the
existing "Don't poll — wait for ping" delegation rule, made concrete for
shared-upstream contention.

### Registry lines appended (S10-SESSION_REGISTRY.md, 20:52–20:59 +07)

- BLOCKER THẬT: HTTP 402 in_flight_budget_exhausted — raw in
  output/s10/c2/t02-c2/dispatch-r1c.log
- ROOT CAUSE: Manager chat session 20260828_180654_be71b5 chạy CÙNG model
  ocg/deepseek-v4-flash qua cùng 9Router/OpenRouter; mỗi poll = 1 request
  ~200k tokens in-flight → worker prefill + Manager requests vượt budget
- POLICY FIX: no manual polling; end turn after dispatch; notify_on_complete
- 20:58:56 +07 — R1d resumed SAME owner SAME prompt SAME model

## 3. Companion observations

- J1-v4 freeze manifest for this cycle:
  `output/s09/20260823_sprint_full/freeze-c4-meta/freeze_manifest_v4_after.json`
  (13 files, 12 LF + composite.py CRLF, HEAD ee10e55a). Re-hash with a small
  Python script (hashlib over raw bytes + `data.count(b"\r\n")`); beware
  `f"{...b'\r\n'...}"` SyntaxError — count outside the f-string.
- Baseline fidelity: C1 review claimed `143 passed, 2 failed`; actual current
  tree ran `145 passed, 0 failed` (196.33s) because a previous T03-C1
  mkdir-parents fix already landed. Record your OWN re-run as ground truth
  and note the discrepancy in the registry (as done above).
- Worker self-labeled `STATUS: TASK_SUBMITTED` with 37/46 tests passing is
  NOT terminal — reject early exits carrying unresolved failures and resume
  the owner with a fix packet that lists each failing test's root cause.
- RULES_LOADED line count + SHA in a worker REPORT is not source data (R4
  claimed 37 dòng / SHA 29ea6b60 vs real 180 / 987386c5). Treat any
  self-reported rules-hash as unverified; gate on disk/test evidence.

## 4. 402 taxonomy: two DIFFERENT 402 bodies (verified 28/08)

Same cycle produced two distinguishable 402 errors — stop vs retry depends
on which one:

1. **Transient — in_flight_budget_exhausted**: `"This request would exceed
   your available credits given your current in-flight requests. Retry after
   in-flight requests settle, or add credits"`, metadata
   `reason: in_flight_budget_exhausted`. → wait 5 min, resume SAME owner /
   SAME prompt / SAME provider-model. NOT a blocker.
2. **Permanent — balance exhausted**: `"This request requires more credits,
   or fewer max_tokens. You requested up to 16384 tokens, but can only afford
   9797."` → account balance gone: request will FAIL until top-up. Rules §7:
   no infinite retry of a certainly-failing request. Terminal
   `BLOCKED_MODEL_ROUTE` (route unavailable due to credit), hand user the
   options: top-up credit / explicit route-change instruction (user override
   mid-cycle is legal per Rules §1.4 — S10-C2's real fix was dispatching the
   FULL model id `ocg/deepseek-v4-flash` on provider `custom` instead of the
   bare `deepseek-v4-flash`, verified via 9Router `kv`/`usageHistory`;
   note the user's phrasing "dùng chính model tôi đang chat với bạn" means
   mirror the chat session's exact provider+model, NOT just switch provider
   aliases — all providers share the same key/base_url, only the model id
   chooses the upstream) / lower max_tokens
   (risky for reasoning-max sessions).

## 5. Throughput: pre-write ALL downstream prompt packets

While the first serial-DAG worker runs, pre-write the remaining
`output/<lane>/prompt.txt` packets for every downstream task (coordination-
only files; zero production write-set touch). Each join gate then opens with
same-turn dispatch instead of a prompt-authoring gap. Include in the packet
for any task whose prior "dispatch" produced no work (only prompt.txt, no
TASK/LOG/REPORT on disk) a note that this is the FIRST real execution —
verify on disk before treating a dispatch as executed.