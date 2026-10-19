# Output ceiling, worker liveness, and safe harness patches (Windows, measured 2026-10-06)

Context: a long-scope worker (`hermes chat -q`, resumed across rounds) died repeatedly
with zero artifacts landed. Three distinct causes were isolated and each fix is a
reusable lever.

## 1. `finish_reason='length'` death loop → raise the per-child output ceiling

Signature (verbatim from the worker log):

```
⚠️  Response truncated (finish_reason='length') - model hit max output tokens
⚠️  Truncated tool call detected — retrying API call (1/4)...   (×4)
⚠️  Truncated tool call response detected again — refusing to execute incomplete tool arguments.
 Response truncated due to output length limit
Resume this session with:
  hermes --resume <sid>
```

exit 0, nothing landed; resuming repeats the death even with a smaller packet.

Diagnosis: the local Hermes config `model.max_tokens` (measured 16384) caps ONE
response's output. The routed model (`cmc/deepseek/deepseek-v4.1-flash` via 9Router)
advertised `maxOutput: 384000`. A reasoning-heavy model can spend most of 16K output
tokens on reasoning + one tool call, so the call truncates mid-emit and the
refuse-incomplete-arguments guard correctly aborts.

The lever — source-verified in the installed runtime (CLI config block in `cli.py`):

```python
# Read max_tokens from config (env var override: HERMES_MAX_TOKENS)
_env_mt = os.environ.get("HERMES_MAX_TOKENS")
if _env_mt:
    self.max_tokens = int(_env_mt)
```

So the launcher sets it for the child process only:

```python
env = dict(os.environ)
env["HERMES_MAX_TOKENS"] = "131072"
subprocess.Popen(argv, env=env, ...)
```

- **Task-local**: does NOT touch global config.yaml / router / other sessions.
- **Calibrate before trusting** (proves the lever is honoured by THIS runtime):
  `HERMES_MAX_TOKENS=24 hermes chat -Q -q "count 1 to 60, one per line"` → output
  truncated at exactly ~24 tokens. If it does not truncate at the tiny value, the
  lever is dead in this build — re-grep the installed source for `HERMES_MAX_TOKENS`.
- Pick the value under the route's advertised `max_completion_tokens`
  (`GET /v1/models`, match the routed model id).
- Measured effect: default 16384 → 6+ truncations per ~8-min death loop, zero bytes;
  131072 → **0 truncations across a 40-min run** with real artifacts landed.

## 2. Windows: workers killed by a desktop-app restart → spawn detached

A child spawned from the terminal tool lives in the Hermes desktop process tree.
When the desktop app restarts/updates, the whole tree dies mid-run: launcher + child
vanish together, the worker log has **no exit trailer**, and the receipt keeps null
exit fields. (Distinguish from truncation death by the trailer: truncation death ends
with `Response truncated due to output length limit` + `Resume this session with:`;
a tree-kill ends mid-stream with nothing.)

Fix — root the run OUTSIDE the app tree via WMI:

```bash
powershell -NoProfile -Command "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='cmd.exe /c <abs-path>\run_w3.cmd'} | Select-Object ProcessId,ReturnValue"
```

Wrapper (`run_w3.cmd`): `cd /d <run dir>`, invoke the venv python with ABSOLUTE paths
for launcher + args, append stdout/stderr to a log (`>> manager\w3_stdout.log 2>&1`).
ReturnValue 0 + a fresh pid = spawned. Then verify: `tail DISPATCH_LEDGER.jsonl`
(dispatch + child_spawned rows), and the heartbeat row shows that exact pid alive.
Keep the wrapper's log append-only; a killed wrapper must not clobber evidence.

## 3. Re-runnable ("idempotent") harness patch scripts

When applying N policy patches to your own harness via a Python script, make the
helper skip patches already applied — otherwise a partial failure followed by a
re-run silently DUPLICATES blocks.

Measured bug class: an append-style patch (`new = old + block`, i.e. `new ⊇ old`) has
`count(old) == 1` still true on re-run, so `bytes.replace` re-appends → a duplicated
block, detectable only by reading the file back.

Helper guard:

```python
c = b.count(old)
if c == 0 and new in b:
    print("SKIP (already applied)", tag); return   # re-run safety
assert c == 1, "PREIMAGE_COUNT=%d %s" % (c, tag)   # refuse ambiguity
b = b.replace(old, new); write; re-read; assert equal
```

After the full run: assert per-block `count == 1`; `py_compile` every patched file;
record pre/post sha256 + byte counts per patch in ONE policy-change report; keep a
byte snapshot of every file BEFORE patching (`evidence/policy-preimage-<date>/` +
manifest) and reference it from the report. If a duplicate was produced, collapse it
with a byte-exact `dup + dup → dup` replace and re-verify count == 1 + `py_compile`.
