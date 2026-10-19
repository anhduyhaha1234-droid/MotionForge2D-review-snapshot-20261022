# S10 Dispatch Pitfalls — prompt file & parallel wave (verified 2026-08-27)

Two dispatch failures hit the S10 W1 pre-dispatch in the same Manager session — both recovered, but each would have silently killed a lane.

## 1. `cat <<'EOF'` heredoc breaks on Vietnamese prompts

**Symptom:** `cat > output/s10/t01a/prompt.txt <<'PROMPT_T01A_EOF'` then writing multi-line
Vietnamese (diacritics + `'` quotes inside the prompt text) died:

```
/usr/bin/bash: -c: line 59: unexpected EOF while looking for matching `''`
```

Root: the shell heredoc delimiter collides with a single-quote `'` inside the
prompt body. The prompt holds lines like `... [OUT-OF-BAND USER MESSAGE]` and
Vietnamese contractions — one stray `'` on any line breaks the heredoc even
though the outer delimiter is quoted.

**Fix that worked in the same session:** abandon heredoc, use a file-write tool
that never touches the shell quoting layer:

```
execute_code: Path(".../prompt.txt").write_text(p1, encoding="utf-8")
# or write_file tool with the full prompt content
```

`p1` is a Python triple-quoted raw string (`r"""..."""`) so interior `'`/`"` are
inert. After the write, `wc -l` + `sha256sum` verified 45 lines (T01A) / 37
lines (T01B) before dispatch.

**Rule to keep:** for prompts carrying Vietnamese text, use `execute_code` /
`write_file` — never `cat <<'EOF'` heredoc. The orchestration skill's
"ALWAYS write the worker prompt to `output/<lane>/prompt.txt`" invariant stays,
but the *mechanism* is file-write tooling, not shell heredoc.

## 2. `terminal` forbids shell `&` backgrounding

**Symptom:**

```
terminal(command="... &", background=true)  →  error: Foreground command uses
'&' backgrounding. Use terminal(background=true) for long-lived processes
```

The runtime rejects `&` inside the command string even when `background=true`
is set. The `&` is redundant — `background=true` is the backgrounding
primitive; a trailing `&` double-backgrounds and is blocked.

**Fix:**

```
terminal(background=true, notify_on_complete=true,
         command="HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes -z \"$(cat .../prompt.txt)\" -m meta --yolo")
```

No `&`, no `|`, just the bare `hermes ...` command. Two parallel T01A/T01B
lanes were launched as two separate `terminal(background=true, ...)` calls —
one per task — which is the approved pattern for a max-2 parallel wave.

## 3. Mid-turn go + ETA must co-occur

The S10 Manager had just anchored `RULES_LOADED` + preflight when two
`[OUT-OF-BAND USER MESSAGE]` arrived in the same underlying turn:
`xong thì estimate ...` and `sao lại dừng r`. The correct response per the
orchestration contract is:

- Report live preflight (HEAD, DB guard) in the *same reply* as the dispatch
  confirmation — do not defer ETA to a later heartbeat.
- State which of the 3 legitimate silence causes applies (here: "workers running
  after dispatch", not "waiting join gate" or "parked at terminal").
- Emit the date-anchored wall ETA table (`PREP → (T01A‖T01B) → … → SPRINT_EXIT`)
  with ideal vs +1-correction columns, so the next `sao thấy dừng rồi?` is not
  repeated.

This pitfall belongs to the Manager cadence section (30' heartbeat + instant on
exit/blocker), not to a generic skill.
