# Mid-sprint worker model override — layered probe protocol (Hermes Manager)

Trigger: the user issues a mid-sprint model override for workers ("đổi worker sang
model X"). Rules §5: model routing is per-prompt, the newest user instruction wins,
fallback OFF means never auto-fallback and never silently auto-correct the
route string. Proven on S10-C6B (override `comboBAI` via 9Router, 2026-08-31).

## Protocol — probe cheapest layer first, keep raw evidence per layer

1. **Catalog**: `GET {base_url}/v1/models` — find the EXACT id (case-sensitive).
   If the user-given string is absent, do NOT silently substitute: probe both the
   user's literal string and the catalog id, and record which one 404s
   (e.g. user typed `comboBai` → 404; catalog `comboBAI` → 200).
2. **Raw chat probe**: `POST /v1/chat/completions` with the API key read from
   `config.yaml` (`providers.<name>.api_key`); prompt
   `"reply with exactly: PROBE_OK"`. Record HTTP status and the gateway-echoed
   upstream `model` field.
   - Gotcha A: 9Router-style gateways append `data: [DONE]` to even non-stream
     JSON responses → strict `json.loads` raises `Extra data`. Strip the
     trailing `data: [DONE]` before parsing; a parse error does NOT mean the
     route failed — read the raw body first.
   - Gotcha B: `Missing API key` authentication_error means the route EXISTS but
     the probe lacked credentials — read the key from config; never print it.
3. **Dispatch probe (end-to-end)**: 
   `hermes -z "Reply with exactly: DISPATCH_PROBE_OK. Do not use any tools." -m <exact-id>`
   — proves the CLI selector actually resolves through the configured provider.
   Use the registry-proven flag order (`-z` prompt first, `-m` model, `--yolo`
   last); inventing extra flags (e.g. `--max-turns 1`) makes argparse consume
   the next token as a subcommand and the probe never runs.
4. **Only after all three pass**: dispatch the real worker with the same exact
   selector and append to the registry: the user override quote, all probe
   outputs (status + effective upstream model), fallback OFF, TTFB env, and the
   case-sensitivity note. Persist the override to durable memory so future
   sessions do not rediscover it by 404.

## Override proven combos + resume-form probe (S10-C6C, 2026-09-01)

- `--provider custom` IS a valid hermes CLI flag and resolves: the C6C packet
  required exact `BAI/glm-5.3-flash --provider custom` and the probe passed in
  both forms (`hermes -z "..." -m BAI/glm-5.3-flash --provider custom --yolo`
  → MODEL_PROBE_OK; the same with `--resume <exact-owner>` → RESUME_PROBE_OK).
  When the packet guesses a different flag order, probe the order you will
  actually dispatch and record the raw logs under
  `output/<round>/manager/prep/model/**` (packet-required evidence location).
- When resuming an exact owner, run the dispatch probe in the RESUME form too,
  not just fresh — cheap (~seconds), and it proves the exact
  `--resume + -m + --provider` combination the real dispatch will use.
- **Overrides rotate per round — never carry the previous round's forward.**
  C6B was `comboBAI` (no --provider needed); C6C's packet then mandated exact
  `BAI/glm-5.3-flash --provider custom` and FORBADE comboBAI. Each new
  correction packet's §model section supersedes everything before it: read the
  packet, re-probe, update memory + crons in the same turn. An override
  recorded in memory is "latest known", not a standing default.

## Effective-route evidence to retain

- The user's literal override string (quote it).
- Catalog id actually used (state any case difference explicitly — do not "fix"
  silently).
- HTTP 200 + upstream model echo (e.g. `comboBAI` →
  `deepseek/deepseek-v4-flash-vision-exp`; `ocg/deepseek-v4-flash` →
  `deepseek-v4-flash` — different upstreams prove the route really changed).
- Dispatch probe output line (`DISPATCH_PROBE_OK`).

## Failure classification

- 404 on the user's literal string with a catalog near-match: probe the catalog
  id; if it works, proceed with the catalog id and note the case difference in
  the registry — this is not a silent model substitution.
- 401/`Missing API key`: credential step missing; fix the probe, not the route.
- 402 credit / in-flight budget errors: transient or account-level; per Rules §7
  wait-and-resume for transient, report `BLOCKED_MODEL_ROUTE` for proven
  balance exhaustion. Do not switch models on your own.
- If the exact user-mandated route is unavailable AND no catalog equivalent
  works: `BLOCKED_MODEL_ROUTE`, never auto-fallback.
