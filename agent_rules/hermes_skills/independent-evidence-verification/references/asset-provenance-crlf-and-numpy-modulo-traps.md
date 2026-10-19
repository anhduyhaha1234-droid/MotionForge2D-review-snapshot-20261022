# Asset Provenance, CRLF Anchors, and NumPy uint8 Modulo Traps

Key failure modes and deterministic workarounds encountered during asset keygen provenance verification (R6/A2) on Windows.

## 1. NumPy uint8 Modulo Overflow in Python 3.11

### Symptom
When generating synthetic image test arrays or applying pixel transformations:
```python
arr = (np.arange(640 * 360 * 3, dtype=np.uint8).reshape(360, 640, 3) + 10) % 256
```
Fails with:
```text
OverflowError: Python integer 256 out of bounds for uint8
```

### Mechanism
In Python 3.11 with modern NumPy, the scalar `256` cannot be represented as an 8-bit unsigned integer (`0..255`). When NumPy attempts to coerce the scalar operand to the array's dtype (`uint8`), Python raises an `OverflowError` before the modulo operation executes.

### Pattern / Workaround
Always upcast to a 32-bit signed integer before arithmetic and modulo, then cast back to `uint8`:
```python
arr = ((np.arange(640 * 360 * 3, dtype=np.int32).reshape(360, 640, 3) + 10) % 256).astype(np.uint8)
```

---

## 2. Mixed CRLF / LF Line Endings in Binary Patch Anchors

### Symptom
An exact binary replacement script asserts `content.count(old_anchor) == 1`, but the assertion fails with `0 == 1`, even though visual inspection of the file shows the anchor text is present.

### Mechanism
Files edited across Git-bash (MSYS), Python, or Windows native tools frequently acquire mixed line endings:
- Consecutive empty lines may contain `\n\r\n\r\n` or `\r\r\n`.
- Some lines end in `\r\n` while edited sections end in `\n`.
Exact byte anchors like `b'COMPLETE_KIND = "..."\r\n'` fail to match `b'COMPLETE_KIND = "..."\n\r\n\r\n'`.

### Pattern / Workaround
1. Inspect the raw bytes around the target anchor using `repr(c[idx:idx+80])` via a quick one-liner.
2. In Python replacement scripts, prefer string mode with explicit line-ending handling:
   ```python
   with open(path, "r", encoding="utf-8") as f:
       content = f.read()  # Python universal newlines normalizes to \n
   # Perform unique substring replacement
   assert content.count(old_str) == 1
   content = content.replace(old_str, new_str)
   with open(path, "w", encoding="utf-8", newline="\n") as f:
       f.write(content)
   ```

---

## 3. Order-of-Evaluation in Legacy Provenance Denial Checks

### Symptom
When testing that a legacy v3 record cannot claim complete v4 skip authority, the test expects an error message like `"legacy v3 lacks complete provenance"`, but receives `"settings changed now: ..."` instead.

### Mechanism
In `skip_allowed()`, shallow settings equality is evaluated *before* the contract version check:
```python
if dep.get("kind") not in (COMPLETE_KIND, COMPLETE_ASSET_KIND):
    try:
        cur = settings_now(sid, fid)
        if dep.get("settings") != cur:
            return False, f"settings changed now: {dep.get('settings')} vs {cur}"
    except Exception as e:
        return False, f"settings unverifiable: {e}"
    return False, "legacy v3 lacks complete provenance"
```
If the test fixture constructs a legacy v3 record with partial or dummy settings (e.g. `{"mode": "...", "steps": 4}`), the settings comparison fails first, masking the provenance contract check.

### Pattern / Workaround
In the test fixture, always query the current canonical settings via `settings_now(sid, fid)` and embed that into the legacy v3 record. This satisfies the settings match and cleanly exercises the `kind` denial branch.

---

## 4. Telegram Heartbeat: HTML vs Markdown Formatting

### Symptom
Sending status updates or filenames containing underscores to Telegram Bot API with `parse_mode="Markdown"` raises:
```text
HTTP Error 400: Bad Request
```

### Mechanism
Telegram's legacy `Markdown` parser (v1) treats bare underscores (`_`) as opening or closing italics. File names like `r6_cache.py`, `f_0001_key.png`, `TASK_C02B2`, or identifiers with underscores break the parser unless every underscore is escaped (`\_`).

### Pattern / Workaround
Use `parse_mode="HTML"`:
- Wrap bold headers in `<b>...</b>`
- Wrap code, variables, and file paths in `<code>...</code>`
- Wrap italics in `<i>...</i>`
- HTML parser does not fail on bare underscores, backslashes, or brackets inside text.
