---
name: llm-provider-verification
description: "Verify model identity on OpenAI-compatible proxy APIs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [llm, providers, api, verification, proxy, relabel, model-identity]
    related_skills: [hermes-config, terminal-engineering-discipline]
---

# LLM Provider Verification

## Overview

When an OpenAI-compatible provider is a **proxy/aggregator/distributor** (e.g. VietAPI, 9Router, or any `custom_providers` entry in Hermes config), the advertised model id is NOT proof of what actually answers. Providers relabel models (observed: GPT-5 variants served as `deepseek-v4-flash` / `deepseek-v4-pro`), list models with no live channel (404), or time out. This skill verifies what actually answers and which models are usable.

## Trigger

- User asks "is this model real?" / "model fake?" / "model gì thật không?"
- Provider is a proxy/aggregator — `/models` shows `owned_by: custom`
- Multiple providers in `config.yaml` (`custom_providers`) and user cares which is trustworthy
- A model self-reports an unexpected identity, or user wants the most stable model

## Workflow

1. **Enumerate** — `GET {base_url}/v1/models` with `Authorization: Bearer <key>`. Note `owned_by: custom` → likely relabel. There is no point trusting the list; probe every id.
2. **Extract key from config** — parse `config.yaml` `custom_providers` blocks with Python regex (per-provider `name` → `base_url` + `api_key`). NEVER print the full key (Hermes redacts secrets in output anyway).
3. **Probe identity** — `POST /v1/chat/completions`, `model=<id>`, user prompt like *"Bạn là model ai và ai tạo ra bạn? Hãy thành thật."*, `max_tokens≈80–120`, `temperature 0`. Read `response.model`, `usage.completion_tokens_details.reasoning_tokens`, `cached_tokens`.
4. **Cross-check** — repeat the identity probe 3× for stability; add a math probe (`17 * 23`) and a language probe (Chinese) to distinguish backends.
5. **Compare siblings** — probe `deepseek-v4-flash`, `deepseek-v4-pro`, `gpt-5.5`, `grok-*` with the same prompt. If several "different" ids all self-identify as Codex/GPT → same GPT backend relabeled. A provider may also serve real DeepSeek under a grok/other id.
6. **Channel health** — classify every id: OK / timeout / 404 "không có channel" / 402 "hệ thống đang bận" / 429 "upstream quá tải". Listed ≠ available.
7. **Batch long runs** — 30 models × 20–25s timeout ≈ 10+ min → run background with `notify_on_complete`, poll, and **report progress + ETA to the user in Vietnamese** (user demands progress reports on long runs; silence reads as a hang).

## Reporting (user preference)

- Respond in Vietnamese with a table: model id → status → self-identity → verdict (real/fake/unstable) → recommendation.
- Report which chunk of the batch finished, what remains, ETA. The user's "làm gì lâu thế / sap xong chua" means: never sit silent on a long batch.
- Recommendation should name a concrete alternative (e.g. local 9Router `ocg/deepseek-v4-flash` already verified, or official provider) rather than "try another".

## Modality capability (vision) verification

Identity is only half of "is this route usable" — a route can answer text correctly and
**silently drop images**. Observed on 9Router (2026-09): HTTP 200 with a normal body whose
content said `image omitted: model has no vision support`, i.e. a green response that never
read a pixel. Three checks, in order:

1. **Metadata** — `GET /v1/models` and read the per-model `capabilities` block
   (`vision`, `tools`, `reasoning`, `thinkingEffortSupported`). For the round above,
   `ocg/deepseek-v4.1-flash` advertised `vision=true, tools=true, reasoning=true,
   thinkingEffortSupported=false` — which is also how you confirm an "effort" field the
   adapter does not expose (record it as `N/A`, do not claim a max-reasoning route).
2. **Live identity** — a real `chat/completions` call; record `response.model`, which is the
   provider's **canonical** upstream name behind the alias (a request for
   `ocg/deepseek-v4.1-flash` returned `"model": "deepseek-v4.1-flash"`). Also note latency:
   a 16-token probe taking ~24 s means a loaded upstream, not a broken route.
3. **Pixel-only proof** — `scripts/vision_nonce_smoke.py` renders a random nonce and a
   shuffled colour order *into the pixels only* and writes the answer to a file it does not
   print. View the PNG natively, state what you see, **then** read the validation file.
   Match on both nonce and order = the image was genuinely read. (Never let the generator
   print the answer before the read — that converts the test into a text-parroting exercise.)

**Metadata can also go silent — do not read `null` as "no capability".** Measured 2026-09-24 on the same
9Router build one round later: `/v1/models` still listed `ocg/deepseek-v4.1-flash` (and `context_length`),
but `vision` / `tools` / `reasoning` / `thinkingEffortSupported` all came back **`null`** for that entry. The
route was in fact working — a fresh nonce image read back correctly and a real tool call succeeded. So when
the capability block is missing/null, read it as *undeclared* and fall back to behavioural proof; never report
`BLOCKED_MODEL_ROUTE` just because a router stopped publishing the flags. Report it as: "metadata does not
declare the capability in this build; capability proven behaviourally by <nonce image read> + <real tool call>".

**Prove the tool channel too, not just vision.** A route can answer text and still mangle tool calls. Use
`scripts/route_probe_raw.py`: it sends one `chat/completions` request with a single function schema and
`tool_choice: "auto"`, then reports `finish_reason`, the count of `tool_calls`, and the **arguments it actually
emitted** — the proof is that the argument equals the value you asked for (e.g. `read_nonce({"nonce":"TOOLRT-7Q2"})`),
not merely that a call appeared. Expect `finish_reason: "tool_calls"` and `response.model` normalised to the
upstream name behind the alias.

**Trailing SSE terminator breaks a naive `json.loads` — decode with `raw_decode`.** The same router appends
`data: [DONE]\n\n` to an otherwise normal JSON body, so `json.loads(body)` raises
`JSONDecodeError: Extra data: line 1 column 612`. This is a body-shape quirk, **not** a route failure: use
`json.JSONDecoder().raw_decode(text)` (first object wins, then stop) or trim the trailing `data: [DONE]` line
before parsing. A probe that reports "Extra data" as an error will read as a broken route when the route is fine.

A config flag alone is never the evidence: the same route that advertised `vision=true`
is only "vision working" after a nonce comes back off the pixels. When a managed route
requires proof before dispatch (see `pm-worker-orchestration` for Manager-side use), record
image **sha256 + frame/observation + the model id that read it** so a reviewer can re-derive
the claim.

**Re-prove it LIVE when asked, never quote an earlier pass.** A resumed/long session may hold a
stale opinion of its own capability, and the user asking *"đã có vision chưa / is vision working
yet?"* is asking about NOW. In that turn: generate a FRESH nonce (`scripts/vision_nonce_smoke.py`
→ new file, stdout redirected so the answer never enters the text context), view it, state what you
read, then diff against the withheld ground truth — and report the new image's sha256 with the
result. Also distinguish the layers, because a route can advertise vision at one layer and drop
images at another: Hermes-side capability (`providers.<name>.models.<id>.supports_vision: true`) is
NOT sufficient on its own — the router/proxy has its own capability resolver, and a vendor patch
targeting that table may be needed before images survive the hop. Check metadata, a live
`response.model`, AND the pixels before saying yes.

When the route is verified, say what it was actually used for. A capability demo is weak evidence
of capability; reading real artifacts (candidate frames vs source frames, contact sheets, UI
screenshots) and writing the observation with image sha256 + frame indices + explicit coverage is
what a reviewer can re-derive — and state the limits plainly (which frames, no playback, no audio)
rather than rounding up to "reviewed the clip".

## Pitfalls

- **Model knowing DeepSeek facts ≠ being DeepSeek** — GPT knows those facts too. The identity self-report is the discriminator, not knowledge answers.
- **Identity varies run-to-run** (router pools backends). 3 consistent answers = signal; 1 inconsistent = unstable.
- **First timeout ≠ dead** — retry once; repeated timeouts (3×) = unreliable, report as such.
- `response.model` in the reply echoes the requested id — **NOT authenticity proof**.
- 404 "không có channel khả dụng" = listed but no backend → skip quickly; 402/429 = quota/busy, may clear later.
- **A 401 is NOT "model dead" — try sibling namespace spellings.** A proxy/aggregator can map the same paper-model under multiple namespace prefixes that resolve differently. Observed on 9Router (2026-08): `meta/muse-spark-1.2-contributor` → HTTP 401 `invalid_api_key` repeatedly, while `ocg/muse-spark-1.2-contributor` → works instantly (same key, same endpoint). When one spelling 401s/404s, diff the live `/v1/models` list for the sibling id and probe IT before declaring the model unusable. Also verify the provider's `api_mode` — a `codex_responses`-mode custom provider may 404 spelling variants that differ only by a stray `.`/`-`.
- **`/v1/models` listings are volatile — re-enumerate before trusting a prior verdict.** The same 9Router list showed `meta/muse-spark-1.2-contributor` at 13:57 (43 models) and dropped all `meta/muse-spark*` entries by 14:16 (41 models) while their `ocg/` aliases stayed. A model seen earlier may vanish or change namespace between sessions; re-query `/models` each time you're about to dispatch a long job.
- Backends shift between sessions — re-probe rather than trusting a prior verdict forever.
- **Windows agent terminal: split `curl | grep` into fetch-then-parse.** A single piped command with complex quoting can be hardline-BLOCKED as malformed even though each half is legal (verified 2026-09-17 on `/v1/models`). Fetch first — `curl -s -m 15 <base>/v1/models -o "$LOCALAPPDATA/Temp/<name>.json"` — then inspect offline via `search_files` or `execute_code` (Python `json.load` + id filter). Assert exact-id presence in code (e.g. `'ocg/deepseek-v4.1-flash' in ids`) rather than eyeballing a 60KB single-line JSON.

## Scripts & References

- `scripts/probe_models.py` — batch-probe every model of a named provider from config.yaml; prints a status table (OK/HTTP/ERR + self-identity + reasoning_tokens).
- `scripts/route_probe_raw.py` — one-shot effective-route probe: `/v1/models` metadata (tolerating `null` flags), a real tool-call roundtrip whose proof is the emitted argument, and a `raw_decode` reader that survives a trailing `data: [DONE]` terminator.
- `scripts/vision_nonce_smoke.py` — generate a synthetic PNG whose nonce/colour order live only in the pixels (answer file is not printed); view natively, then compare. Proves a proxied route actually accepts image input.
- `references/vietapi-audit-2026-08.md` — full VietAPI 30-model audit results (status, self-identity, verdicts).