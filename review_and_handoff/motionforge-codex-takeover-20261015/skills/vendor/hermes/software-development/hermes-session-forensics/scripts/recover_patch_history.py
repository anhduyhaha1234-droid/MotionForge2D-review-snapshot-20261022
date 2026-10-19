#!/usr/bin/env python3
"""Recover a file destroyed by an agent from Hermes session DB tool history.

Usage:
  python recover_patch_history.py <state.db> <target_file_abs_path> <output_py>

What it does:
  1. Finds the earliest write_file whose arguments 'path' == target file (base).
  2. Walks every assistant message with patch tool_calls referencing the file,
     in rowid order; resolves success ONLY via role='tool' effect_disposition.
  3. Applies old_string -> new_string when old is found.
  4. For unfound (drift-skipped) successful patches, collects every top-level
     'def' block from new_string (col-0) so function bodies survive even when
     the chain diverges. NEWEST block wins per name.
  5. Writes base + (in-order) applied patches + col-0 blocks + staged sections
     (list extra sections in EXTRA_SECTION_MSG_IDS if you know them) to output.

Notes:
  - Every applied edit is in your OWN session DB only if the agents ran on this
    machine's Hermes store (CLI/desktop sessions share ~/AppData/Local/hermes).
  - Verify the result with py_compile and, for tests, compare symbol names
    against __pycache__ ground truth (see SKILL.md recipe).
  - Dots in the output filename break pytest collection: use underscores.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

# Message ids of "staged section" write_file/execute_code calls (outside the
# target file) discovered by searching for distinctive function names, e.g.:
#   SELECT id, tool_calls FROM messages
#   WHERE role='assistant' AND tool_calls LIKE '%<func_name>%' AND tool_calls LIKE '%write_file%'
# Fill this list after inspecting those calls. Empty by default.
EXTRA_SECTION_MSG_IDS: list[int] = []


def load_calls(raw: str) -> list[dict]:
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return data


def get_args(call: dict) -> dict:
    fn = call.get("function") or {}
    if not isinstance(fn, dict):
        return {}
    try:
        return json.loads(fn.get("arguments") or "{}")
    except Exception:
        return {}


def extract_top_level_def_blocks(text: str) -> dict[str, str]:
    """name -> block for every col-0 'def name(...)' block in text (newest wins)."""
    out: dict[str, str] = {}
    for m in re.finditer(r"(?m)^def (\w+)\(", text):
        name = m.group(1)
        seg = text[m.start():]
        end = re.search(r"(?m)^def (\w+)\(", seg[1:])
        out[name] = (seg if not end else seg[:end.start() + 1]).strip()
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    db_path, target, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    con = sqlite3.connect(db_path)

    # 1) base = earliest write_file matching target
    base = None
    for r in con.execute(
        "SELECT id, tool_calls FROM messages WHERE role='assistant' AND tool_calls LIKE ? ORDER BY rowid",
        (f"%{Path(target).name}%",),
    ):
        for c in load_calls(r[1]):
            fn = c.get("function") or {}
            if fn.get("name") != "write_file":
                continue
            a = get_args(c)
            if str(a.get("path", "")).replace("\\", "/") == target.replace("\\", "/"):
                base = a.get("content") or base
    if not base:
        print("base write_file not found; is this target owned by the agents on this store?")
        return 1
    print(f"base {len(base)} bytes")

    # 2) success map
    disp = {}
    for r in con.execute(
        "SELECT tool_call_id, effect_disposition FROM messages WHERE role='tool' AND tool_call_id IS NOT NULL"
    ):
        if r[0]:
            disp[r[0]] = r[1]

    content = base
    blocks: dict[str, str] = {}
    applied = skipped = failed = 0
    rows = con.execute(
        "SELECT rowid, tool_calls FROM messages WHERE role='assistant' AND tool_calls LIKE ? "
        "AND tool_calls LIKE '%patch%' ORDER BY rowid",
        (f"%{Path(target).name}%",),
    )
    for r in rows:
        for c in load_calls(r[1]):
            fn = c.get("function") or {}
            if fn.get("name") != "patch":
                continue
            cid = c.get("id") or c.get("call_id") or ""
            a = get_args(c)
            if str(a.get("path", "")).replace("\\", "/") != target.replace("\\", "/"):
                continue
            if disp.get(cid) and disp[cid] != "success":
                failed += 1
                continue
            old, new = a.get("old_string", ""), a.get("new_string", "")
            if not old:
                continue
            idx = content.find(old)
            if idx != -1:
                content = content[:idx] + new + content[idx + len(old):]
                applied += 1
            elif new:
                for name, block in extract_top_level_def_blocks(new).items():
                    blocks[name] = block
                skipped += 1
    print(f"applied={applied} skipped={skipped} failed={failed} blocks={len(blocks)}")

    # 3) staged sections
    for mid in EXTRA_SECTION_MSG_IDS:
        row = con.execute("SELECT tool_calls FROM messages WHERE id=?", (mid,)).fetchone()
        if not row:
            continue
        for c in load_calls(row[0]):
            fn = c.get("function") or {}
            a = get_args(c)
            if fn.get("name") == "write_file":
                blocks.update(extract_top_level_def_blocks(a.get("content", "")))
            elif fn.get("name") == "execute_code":
                for m in re.finditer(r"(?m)^def (\w+)\(", a.get("code", "")):
                    pass  # execute_code bodies usually embedded as strings; handle per case

    merged = content.rstrip() + "\n\n" + "\n\n".join(blocks.values()) + "\n"
    Path(out_path).write_text(merged, encoding="utf-8")
    tests = re.findall(r"(?m)^def (test_\w+)\(", merged)
    print(f"wrote {out_path}: {len(merged)} bytes, {len(tests)} test defs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
