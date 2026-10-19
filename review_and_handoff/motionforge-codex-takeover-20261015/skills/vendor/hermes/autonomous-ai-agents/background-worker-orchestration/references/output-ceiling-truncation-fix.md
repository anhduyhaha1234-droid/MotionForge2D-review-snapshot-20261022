# Truncation death loop: fix the OUTPUT CEILING, don't just re-resume

Measured 2026-10-06 (MF-DEMO-LONG-01, Windows, custom 9Router route). A `hermes chat`
worker died **twice in a row** — W0 after 18 min, W1 after 8.5 min — both ending with:

```
Response truncated (finish_reason='length') - model hit max output tokens
Truncated tool call detected — retrying API call (1/4)... (4/4)
Truncated tool call response detected again — refusing to execute incomplete tool arguments.
Response truncated due to output length limit
Resume this session with:  hermes --resume <sid>
```

W1 landed **zero new durable artifacts** in 8.5 minutes. The wrong response is
"resume again" — the model emits long reasoning + large tool-call payloads in one
completion; a low output ceiling cuts the tool call mid-emit; Hermes refuses the
incomplete args and the turn dies. Re-resuming with the same ceiling reproduces it forever.

## Diagnose before deciding (count, don't guess)

```bash
grep -ac "finish_reason='length'" worker.log                    # ceiling deaths
grep -acE "503|502|UsageLimit|API call failed" worker.log       # infra / quota flaps
```

`finish_reason` deaths with **0** infra errors ⇒ it is a *ceiling* problem, NOT a
transient flap. Do NOT apply the 5-min backoff/retry cycle (that wastes cycles on
a configuration bug). Truncation ≠ quota: no 503/502/UsageLimit anywhere.

## Root cause this run

- Hermes `config.yaml`: `model.max_tokens: 16384` — the effective per-completion output ceiling.
- The route advertised `maxOutput: 384000` (via `/v1/models` capabilities), so the
  model was NOT the limit; the **local config** was.
- The flash model's reasoning + tool args routinely exceed 16K tokens → guaranteed truncation.

## The lever (verified in runtime source)

`HERMES_MAX_TOKENS` env var overrides `model.max_tokens` **per child process**.
Provenance: `cli.py` (site-packages) ~line 4352 reads:

```python
# Read max_tokens from config (env var override: HERMES_MAX_TOKENS)
_env_mt = os.environ.get("HERMES_MAX_TOKENS")
if _env_mt:
    self.max_tokens = int(_env_mt)
```

Wire it in the launcher, task-locally for the child only (satisfies "don't change
global model/router/config to fix one task"):

```python
max_tokens = extra[extra.index("--max-tokens") + 1] if "--max-tokens" in extra else "131072"
...
env = dict(os.environ)
env["HERMES_MAX_TOKENS"] = max_tokens   # e.g. "131072"
subprocess.Popen(argv, env=env, ...)
```

Choose a ceiling below the route's advertised maxOutput but far above typical
completion size (this run: 131072 against a 384000 ceiling).

## Prove the lever before trusting it (saturation probe)

```bash
HERMES_MAX_TOKENS=24 hermes chat -Q -q "Count from 1 to 60, one number per line, nothing else."
```

Expected: output visibly cut at ~24 tokens + `Response remained truncated after N
continuation attempts`. If it cuts at 24, the env var is honoured and the ceiling is
the actual control. Run this probe against the SAME route/model before a long dispatch.

## Evidence after the fix (same worker, same route)

- Truncations in the next invocation: **0** (was 6+ per invocation before).
- Artifacts landing again within minutes (`P1_cuts.json`, 37,918 B, 225 shots,
  coverage [0,39634) int frames) — two prior attempts with the low ceiling had produced nothing.
- The run then continued for hours (54 chunks / 8,827 frames of GPU work) with no truncation loop.

## Bundled harness changes (part of the same policy: per-invocation limits are not task terminals)

- Default `--max-turns` raised (400 → 1000). A max-turns hit is not a task terminal:
  checkpoint, confirm the old writer is terminal, resume the SAME owner session.
- Old total-deadline `proc.wait(timeout=remaining)` replaced by a hang-guard timeout
  (`MAX_INVOCATION_S`, e.g. 6h) so a genuinely HUNG child still dies but a long-running
  one is not stopped by the old budget.
- Resume packets must carry the anti-truncation discipline too (small scripts via
  write_file, ≤200-char commands, short reasoning, no giant inline payloads) — belt and braces.

## Rules

1. Repeated `finish_reason='length'` deaths = configuration bug. Measure the ceiling first.
2. Prefer the env-var override; editing `config.yaml` changes every session on the machine.
3. Resume-after-truncation with the SAME ceiling is a blind retry. After two identical
   deaths, change the ceiling (or shrink payloads) — resuming alone does not fix it.
4. Keep both levers documented in the resume packet: (a) raise ceiling, (b) shrink payloads.
