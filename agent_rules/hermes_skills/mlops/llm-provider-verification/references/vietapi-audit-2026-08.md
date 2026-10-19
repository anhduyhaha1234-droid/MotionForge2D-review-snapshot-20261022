# VietAPI 30-Model Audit — 2026-08-19

Provider: `https://api.vietapi.tech/v1` (Hermes `custom_providers` name `VietAPI`, `owned_by: custom` in `/models`).

Prompt used: *"Trả lời bằng 1 câu: bạn là model ai và ai tạo ra bạn? Hãy thành thật."* (`max_tokens=80`, `temperature=0`). Verified with `scripts/probe_models.py`.

## Verdict

VietAPI is a **proxy distributor, not a genuine model provider**. No model id self-identifies correctly.

## Results

| Model id | Status | Latency | Self-identity | Verdict |
|---|---|---|---|---|
| `claude-fable-5` | HTTP 404 | 1.3s | — | no channel |
| `bedrock-claude-fable-5` | HTTP 404 | 0.3s | — | no channel |
| `cc-max-claude-opus-4-7` | HTTP 404 | 0.4s | — | no channel |
| `cc-max-claude-opus-4-8` | HTTP 404 | 0.3s | — | no channel |
| `cc-max-claude-opus-5` | HTTP 404 | 0.3s | — | no channel |
| `cc-max-claude-sonnet-5` | HTTP 404 | 1.4s | — | no channel |
| `claude-opus-5` | timeout | 22.2s | — | unreliable |
| `claude-opus-5-thinking` | timeout | 22.2s | — | unreliable |
| `claude-opus-4.8` | timeout | 22.2s | — | unreliable |
| `claude-opus-4.8-thinking` | timeout | 22.2s | — | unreliable |
| `claude-opus-4.7` | timeout | 22.2s | — | unreliable |
| `claude-opus-4.7-thinking` | timeout | 22.2s | — | unreliable |
| `claude-opus-4.6` | timeout | 23.3s | — | unreliable |
| `claude-opus-4.6-thinking` | timeout | 22.4s | — | unreliable |
| `claude-sonnet-5` | timeout | 23.4s | — | unreliable |
| `gpt-5.6-sol` | timeout | 22.6s | — | unreliable |
| `gpt-5.6-terra` | OK | 5.8s | Codex (OpenAI) | relabel |
| `gpt-5.6-luna` | OK | 2.7s | ChatGPT (OpenAI) | relabel |
| `gpt-5.5` | timeout | 22.2s | — | unreliable |
| `gpt-5.5-high` | timeout | 23.4s | — | unreliable |
| `gpt-5.5-xhigh` | timeout | 22.2s | — | unreliable |
| `deepseek-v4-flash` | timeout | 22.3s | — | unreliable (this session's model) |
| `deepseek-v4-pro` | OK | 8.0s | **Codex GPT-5 (OpenAI)** | **relabel — NOT DeepSeek** |
| `glm-5.2` | OK | 4.2s | dots (rednote) | relabel |
| `glm-5.3` | HTTP 402 | 1.3s | — | busy/quota |
| `kimi-k2.6` | HTTP 429 | 20.6s | — | quota exhausted |
| `kimi-k3` | HTTP 402 | 1.3s | — | busy/quota |
| `qwen-3.8-max` | HTTP 402 | 0.7s | — | busy/quota |
| `grok-4.6` | OK | 6.7s | **DeepSeek-V3.2** | **likely real DeepSeek** (rt=85) |
| `grok-4.5` | OK | 8.5s | DeepSeek-R1 / Auto-Cursor | **unstable** (2 different answers) |

## Key findings

1. **`deepseek-v4-pro` self-identifies as "Codex based on GPT-5, created by OpenAI"** — the advertised id is a GPT-5 variant, not DeepSeek. Same for `gpt-5.6-terra/luna` (all Codex-family).
2. **`grok-4.6` is the only model that consistently self-identifies as DeepSeek** (3/3 probes: V3.2) and has `reasoning_tokens` — plausibly real DeepSeek relabeled under a grok id. Unconfirmed.
3. **`grok-4.5` is unstable** — answered DeepSeek-R1 on one probe, Auto/Cursor on another.
4. **Claude models are all dead** — 5 ids 404, 12 ids timeout. Do not rely on VietAPI for Claude.
5. **`deepseek-v4-flash` (this session's model) times out** — currently unusable from this endpoint.
6. Knowledge probes (e.g. "who created DeepSeek") are **not** a discriminator — GPT knows DeepSeek facts too.

## Recommendation

For trustworthy DeepSeek: use **9Router local** (`http://127.0.0.1:20128/v1`, model `ocg/deepseek-v4-flash`) — already verified working, or the official DeepSeek API. VietAPI is not recommended for production.