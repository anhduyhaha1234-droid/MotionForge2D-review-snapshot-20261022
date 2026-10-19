# Mnemosyne Migration — legacy MEMORY.md/USER.md → Mnemosyne SQLite (verified 2026-08-27)

Source: live migration on this machine (Windows 11, Hermes 0.19.0, mnemosyne-memory 3.15.1, Python 3.11.9).

## Legacy memory layout

```
<HERMES_HOME>/memories/MEMORY.md   # 9 entries on this host, `§` delimiter
<HERMES_HOME>/memories/USER.md     # 5 entries, same delimiter
<HERMES_HOME>/state.db             # session history (not migrated)
<HERMES_HOME>/mnemosyne/data/mnemosyne.db  # Mnemosyne BEAM SQLite
```

- `HERMES_HOME` on Windows is `C:\Users\<user>\AppData\Local\hermes` (native Windows path). MSYS `~/.hermes` resolves to `/c/Users/...` and mismatches — always probe `HERMES_HOME` env var or `DEFAULT_DB_PATH`.
- `MEMORY.md`/`USER.md` are **not** line-delimited — entries split on `§` (U+00A7), trimmed. Each chunk is one fact.
- `mnemosyne-memory-override` skill marks legacy `memory` tool as deprecated for durable facts.

## Mnemosyne SQLite tables (beam mode)

```
working_memory   # hot, FTS5 + vec, TTL-based, auto-injected
episodic_memory  # long-term, hybrid search
memories         # legacy table — `get_stats().total_memories` counts THIS, not working_memory
memory_embeddings
vec_working / fts_working / vec_episodes / fts_episodes / etc.
```

**Pitfall:** Deleting from `working_memory` alone leaves orphans in `memories` and `memory_embeddings`. `get_stats()` will still report the old count.

## Verified migration recipe

```python
import pathlib
from mnemosyne import remember, get_stats

HERMES_HOME = pathlib.Path(r"C:/Users/Admin/AppData/Local/hermes")
def entries(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    return [s.strip() for s in txt.split("§") if s.strip()]

all_entries = [(e, "MEMORY.md") for e in entries(HERMES_HOME / "memories/MEMORY.md")] \
            + [(e, "USER.md")   for e in entries(HERMES_HOME / "memories/USER.md")]

import sqlite3
db = str(HERMES_HOME / "mnemosyne/data/mnemosyne.db")
existing = {r[0].strip() for r in sqlite3.connect(db).execute("SELECT content FROM working_memory")}
for content, src in all_entries:
    if content.strip() in existing:
        continue
    imp = 1.0 if "CRITICAL" in content else 0.92 if src == "USER.md" else 0.9
    if "Mnemosyne" in content:
        imp = 0.6
    remember(content.strip(), importance=imp, source=src)

print(get_stats())  # expect working_memory == memories == len(all_entries)
```

Verification:

```bash
python -c "from mnemosyne import recall; print(recall('GPM Login', top_k=1))"
python -c "import sqlite3; db=r'C:/Users/Admin/AppData/Local/hermes/mnemosyne/data/mnemosyne.db'; c=sqlite3.connect(db).cursor(); c.execute('SELECT source, count(*) FROM working_memory GROUP BY source'); print(c.fetchall())"
# expect [('MEMORY.md', 9), ('USER.md', 5)]
```

## Demo-data cleanup (verified)

Demo entries created via `remember("User prefers Vietnamese...")` landed in **three** tables. Full cleanup:

```python
import sqlite3
db = r"C:/Users/Admin/AppData/Local/hermes/mnemosyne/data/mnemosyne.db"
conn = sqlite3.connect(db); cur = conn.cursor()
for _id in ["d8dc6c7607433a04", "c8dc2eddfc6b98d9", "e283c770bb27e789"]:
    cur.execute("DELETE FROM working_memory WHERE id=?", (_id,))
    cur.execute("DELETE FROM memories WHERE id=?", (_id,))
    try: cur.execute("DELETE FROM memory_embeddings WHERE memory_id=?", (_id,))
    except: pass
conn.commit()
```

Check zero rows remain: `SELECT count(*) FROM working_memory WHERE content=?` and `FROM memories WHERE content=?` both 0.

## When to migrate

- One-time after `mnemosyne-hermes install` + `hermes config set memory.provider mnemosyne`.
- Keep `MEMORY.md`/`USER.md` as backup — do not auto-delete. Future durable writes go to Mnemosyne only.
