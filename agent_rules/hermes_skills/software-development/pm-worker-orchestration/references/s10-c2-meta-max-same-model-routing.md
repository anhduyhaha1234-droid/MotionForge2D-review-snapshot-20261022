# S10-C2 Meta-max Same-Model-As-Chat Routing (verified 29/08)

Session `20260828_180654_be71b5` — user corrections "dùng chính model tôi đang chat với bạn" / "đổi worker sang model Meta-max giống bạn".

## Why this exists
Prompt S10-C2 mandated `deepseek-v4-flash` via 9Router `ocg/deepseek-v4-flash` (reasoning max, fallback OFF, TTFB 900). Every dispatch with a BARE model id (`-m deepseek-v4-flash`) silently resolved to the WRONG upstream and burned the entire lane before producing a byte.

## Verified 9Router routing matrix (read from `db/data.sqlite` kv + probe)

| Dispatch string | 9Router kv key | providerAlias | Upstream | Probe result | Prefill result |
|---|---|---|---|---|---|
| `--provider custom -m deepseek-v4-flash` | `deepseek-v4-flash` | `cmc` | OpenRouter `openrouter/deepseek-v4-flash` | pong (tiny) | HTTP 402 `in_flight_budget_exhausted` / `Prompt tokens 64350>58353` |
| `--provider custom -m ocg/deepseek-v4-flash` | `ocg|deepseek-v4-flash|llm` | `ocg` | opencode-go (`anhduyhaha`/`duyeco`/`mail 1`, 1945 successes) | `pong ✅` | OK (T02-C2 R4: 46/46×2) |
| `-m deepseek-v4-flash` (no provider) | — | — | — | `No usable credentials for provider 'deepseek'` | n/a |
| `--provider muse -m ocg/muse-spark-1.2-contributor` | `ocg|muse-spark…` | `ocg` | opencode-go | HTTP 404 `No active credentials for provider: opencode-go` (29/08) | — |
| `--provider opencode -m ocg/muse-spark-1.2-contributor` | same | `ocg` | opencode-go | same 404 | — |
| `--provider custom -m meta` | combo `meta` | `meta` | round-robin `cmc/meta/muse-spark` + `ocg/muse-spark` | `pong` (Discipline loaded) | OK (used for T01C-C4 retry) |

Source: `kv` table (keys `deepseek-v4-flash`, `ocg|deepseek-v4-flash|llm`, `ocg|muse-spark-1.2-contributor|llm`), `providerConnections` (3× `opencode-go` active), `usageHistory` (model=deepseek-v4-flash provider=opencode-go 1945), live probes at 22:35/00:35.

## Rule
Worker route = **exact provider+model pair of the manager chat**. Never strip the `ocg/` prefix, never translate `meta`→`muse`, never fall back to `cmc`/OpenRouter. Before ANY dispatch:

```
hermes --provider <p> -m <m> -z "ping" --yolo   # must pong; tiny ping ≠ prefill guarantee
```

Record as `USER MODEL OVERRIDE C2-vX: <provider>/<model>` in `S10-SESSION_REGISTRY.md` with pong evidence. When user says "bỏ hết các model khác nhất là openrouter" treat as hard constraint — no `openrouter`/`cmc`/bare-id outside the chosen pair.

## Companion incident
`in_flight_budget_exhausted` 402 = manager + worker sharing same OpenRouter budget (manager ~215k in-flight tokens per turn). Fix: dispatch → end turn (no polling), `notify_on_complete=true`, wait 5' on 402, resume same owner. See `s10-c2-deepseek-route-and-inflight-402.md`.

## False report to ignore
Worker REPORT `RULES_LOADED SHA 29ea6b60, 37 dòng` vs real `987386c5, 180 dòng` — gate on real test evidence, log in registry for Codex review, don't fail J1 on it.
