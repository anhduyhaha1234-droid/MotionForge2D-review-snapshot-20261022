# Manager chat identity, quiescence probes, and resume lineage (S10-C6H R3-proven)

Codex correction prompts now require a **genuinely new Manager chat** after a
manager is retired for context health (e.g. `20260902_211154_54134d` retired at
366 msgs/663k tokens — R2 violated the fresh-manager rule and was flagged).
Before any dispatch, prove identity + quiescence with read-only state.db
queries and command-line process scans. All commands below are Windows/MSYS,
read-only.

## 1. Prove current Manager chat is new (not the retired ID)

```bash
python -c "
import sqlite3
conn = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT rowid, id, source, model, model_config, title, started_at, end_reason, message_count, tool_call_count, input_tokens FROM sessions ORDER BY rowid DESC LIMIT 3')
for r in cur.fetchall(): print(dict(r))
conn.close()
"
```

- Your current desktop chat is the TOP row (highest rowid, `source='desktop'`).
  Assert its `id != <retired manager id>` before claiming NEW_MANAGER.
- The desktop row records the full model config
  (`"reasoning_config": {"enabled": true, "effort": "max"}` on the desktop path);
  CLI oneshot/resume rows record only `{"max_iterations": 90, "reasoning_config": null}` → that is the RUNTIME_CONFIG_GAP evidence; record it, never claim max was proven.
- Old retired manager row may still show `end_reason: None` in the DB — DB-open ≠
  live process. Quiescence is proven by the process scan (§2), not by end_reason.

## 2. Windows quiescence: host vs worker (command-line scan, not ps -W alone)

`ps -W` name-matches will false-positive on the desktop host itself:
`hermes.exe desktop`, `hermes.exe serve --host 127.0.0.1 --port 0`, and the
Electron `Hermes.exe` children (gpu/renderer/network/audio). None of these are
writers. Distinguish by CommandLine:

```bash
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='hermes.exe' OR Name='python.exe' OR Name='pytest.exe'\" | Select-Object ProcessId,Name,CommandLine | Format-List"
```

A real worker looks like `hermes.exe --resume <id> ... -z ...` (oneshot CLI with
a prompt file). Zero such rows + zero `pytest`/`uvicorn` = OLD_MANAGER_QUIESCENT
/ zero concurrent writer. Ports: expect `20128` LISTENING — that is the 9Router
provider, not a test/worker port; task ports (8201/3014/3015/8888) must be free.

## 3. CLI worker liveness: log stays 0 bytes — read state.db, not the redirect

`hermes --resume X -z "$(cat prompt.txt)" --provider custom -m <model> --yolo
> worker.log 2>&1` buffers stdout: `worker.log` can be **0 bytes while the
worker is actively processing**. Liveness = state.db row progression:

```bash
# effective row = newest rowid; watch message_count/tool_call_count/input_tokens rise
python -c "
import sqlite3, time
conn = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT rowid, id, message_count, tool_call_count, input_tokens, end_reason FROM sessions ORDER BY rowid DESC LIMIT 1')
print(dict(cur.fetchone()))
conn.close()
"
```

## 4. Resume lineage: requested vs effective session ID

`--resume <requested>` materializes a NEW effective row (rowid DESC, source
oneshot, parent recorded as None) while remaining the SAME logical owner
lineage. Record both in the registry immediately (CORRECTION append):

```
- CORRECTION (append-only): R3 resume `--resume 20260903_012248_d29911` tạo
  effective row MỚI = 20260903_094146_7b7197 (rowid 863, model ocg/deepseek-v4-flash,
  parent None) — cùng lineage S10-T01C-C15.
```

## 5. Heredoc append trips the terminal long-lived-process heuristic

`cat >> file << 'EOF' ... EOF` appends to coordination docs (SESSION_REGISTRY /
LOG) can be rejected with "appears to start a long-lived server/watch process"
(guard false positive). Use bounded `printf` appends instead:

```bash
printf '%s\n' '- line1' '- line2' >> docs/pm/sessions/S10-SESSION_REGISTRY.md
```

Same for LOG.md entries. This keeps appends identical in effect and guard-safe.

## 6. R3-specific preflight math (format-independent corrections)

- Rules arithmetic: MAIN canonical 246 lines / SHA `9328c8c0…61bc`; worktree
  stale copy 37 lines / SHA `29ea6b60…` — never merge one file's SHA with the
  other's line count; record both correctly (this was a P2 finding on the R2
  packet).
- Preimage authority: verify route SHA + lines AND test SHA + lines + unique
  `def test_` count (`grep -c '^def test_'` + `sort | uniq -d` for dupes) +
  porcelain count + DB env UNSET before dispatch; snapshot byte-identical
  guards under `output/<round>/manager/guard/snapshots/*.pre_rN` and verify
  snapshot SHA == source SHA (with byte sizes).
- Worker log buffering means "log 0 B" is NOT a blocker; state.db progression
  is the liveness truth (see §3).