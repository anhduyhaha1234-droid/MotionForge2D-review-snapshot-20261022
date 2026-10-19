# Mnemosyne + Hermes — verified setup (2026-08-27, Windows 11, Hermes 0.19.0, Python 3.11.9)

Source: live install on this machine — `pip show`, `mnemosyne-hermes install/status`, `hermes memory status`, `remember/recall` round-trip.

## Install (single Python — no venv split on this host)

```bash
pip install "mnemosyne-memory[embeddings]"   # 3.15.1 — core PyYAML only, [embeddings] adds fastembed 0.8.0 + sqlite-vec 0.1.9
pip install mnemosyne-hermes==0.5.0          # plugin wrapper, depends on mnemosyne-memory>=3.11.1
mnemosyne-hermes install                     # symlink C:\Users\<user>\AppData\Local\hermes\plugins\mnemosyne -> site-packages/mnemosyne_hermes
                                             # + skill at <HERMES_HOME>/skills/memory/mnemosyne-memory-override/SKILL.md
hermes config set memory.provider mnemosyne
hermes memory status                         # Provider: mnemosyne / Plugin: installed ✓ / Status: available ✓
mnemosyne-hermes status                      # State: installed / Mode: symlink
```

Pre-install signal: `hermes memory status` shows `Provider: (none — built-in only)` and plugin list lacks `mnemosyne`; `pip show mnemosyne-memory` = NOT FOUND; `python -c "import mnemosyne"` = ModuleNotFoundError.

## Verification — real DB round-trip (not just import)

```bash
python -c "from mnemosyne import remember, recall; remember('User prefers Vietnamese', importance=0.95); print(recall('Vietnamese', top_k=1))"
# First recall downloads bge-small-en-v1.5 (5 HF files, ~8s unauthenticated) to HF cache — subsequent instant.
# DB: <HERMES_HOME>/mnemosyne/data/mnemosyne.db  (978 KB after 3 memories, beam mode)
python -c "from mnemosyne import get_stats; print(get_stats())"
# -> {'total_memories': 3, 'mode': 'beam', 'beam': {'working_memory': {...}, 'episodic_memory': {...}}}
mnemosyne stats
mnemosyne doctor          # read-only health check
```

## Config

```yaml
# C:\Users\<user>\AppData\Local\hermes\config.yaml
memory:
  provider: mnemosyne
```

`HERMES_HOME` on Windows = `C:\Users\<user>\AppData\Local\hermes` (not MSYS `~/.hermes` which resolves to `/c/Users/...` — use native path for probes).

## CLI surface

- `mnemosyne store/recall/update/delete/stats/sleep/doctor/repair/export/import/bank/reindex/backup/sync/mcp`
- `mnemosyne-hermes install|uninstall|status|cleanup|upgrade`
- `hermes memory setup|status|off|reset` — after install `setup` lists mnemosyne as local provider.

## Pitfalls seen

1. `mnemosyne-memory` core alone has NO vector search — need `[embeddings]` or remote `MNEMOSYNE_EMBEDDING_API_URL`.
2. Legacy `memory` tool is deprecated for durable facts — `mnemosyne-memory-override` skill enforces Mnemosyne. Don't use `memory(action="add")` for preferences/credentials.
3. First-run HF download is unauthenticated (rate-limited) — set `HF_TOKEN` for faster.
4. `HERMES_HOME` mismatch between MSYS bash (`/c/Users/...`) and Windows native (`C:\Users\...`) — verify DB path via `python -c "from mnemosyne.core.memory import DEFAULT_DB_PATH; print(DEFAULT_DB_PATH)"`.
