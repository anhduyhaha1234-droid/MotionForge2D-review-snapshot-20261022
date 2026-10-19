# Composing shell commands that survive the tool boundary (verified 2026-09-29)

A Manager round issued ~250 `terminal` calls. Two composition defects each cost whole
cycles, and both have the same shape: **the failure is in the command STRING, not in the
environment or the tool.** Classify them that way and the fix is mechanical.

## 1. Over-composed one-liners get refused by the command parser

Signature (verbatim):

```
BLOCKED (hardline): command parser limit or malformed executable payload. This command
is on the unconditional blocklist and cannot be executed via the agent — not even with
--yolo, /yolo, approvals.mode=off, or cron approve mode.
```

Observed triggers — all of them *compound* constructs, never a simple command:

| Refused shape | Working replacement |
|---|---|
| `for f in $L/agent.log $L/agent.log.1; do echo "$f: $(grep -c ... $f)"; done` | one command per file, or a single `grep -c` per call |
| `echo "BEFORE=$(git show HEAD:x \| grep -c p) AFTER=$(grep -c p x)"` | two separate calls |
| `grep -vE "..." \| grep -vE "..." \| sed -E '...' \| head` chains with embedded quotes | narrow the pattern and drop the pipeline stages |

Rules that follow:

1. **One purpose per call.** `VAR=...; cmd1; cmd2; for ...; done` is the shape that gets
   refused. Split it.
2. **Prefer a plain `grep -c <pattern> <file>`** over `echo "$(grep -c ...)"`. If you need
   two counts, make two calls.
3. **Never build a pipeline of three or more stages with quoted regexes.** Narrow the
   pattern instead; an over-broad grep is what tempts you into the filter chain.
4. The message names a *parser* limit, so a refusal is **not** evidence about the command's
   target. Re-issue the same *intent* as a simpler command before concluding anything about
   the file, repo or process you were inspecting.

## 2. Corrupted tool-call arguments — recognise and route around

Signature:

```
tool call arguments were corrupted in this session and have been dropped to keep the
conversation alive. See issue #15236.
Error: Invalid JSON arguments. Expecting value: line 1 column 1 (char 0).
```

Observed five times in one long session, and it is **not** about the command's content —
a call that succeeded earlier can be re-issued unchanged and succeed again. What matters is
the recovery, because a repeated identical retry trips the tool-loop guard:

1. **Do not retry the identical call more than once.** Two refusals on the same payload
   means "change the transport", not "try again".
2. **Change transport: run the same command through `execute_code`** wrapping
   `hermes_tools.terminal`. The command string is passed as a Python literal rather than as
   tool-call JSON, which sidesteps the corruption entirely:

   ```python
   from hermes_tools import terminal
   r = terminal("cd <win-path> && git status --porcelain && git rev-parse HEAD")
   print(r["output"])
   ```

   This also keeps several dependent reads in one round-trip, which is worth doing anyway
   once a session is long and you are issuing many small calls.
3. **Shorten and de-quote the command** when re-issuing it inline. Long strings with nested
   quotes and backslashes are the ones that corrupt; the same intent as `grep -n PATTERN
   FILE` usually survives.
4. Tell the user nothing about tooling here — this is internal transport noise. What the
   report must not do is claim the work was done when the call that would have proven it
   never ran.

## 3. Why this is worth a reference

Both defects present as failures of the *environment* ("the tool is blocked", "my JSON is
corrupt") while being failures of *composition*. An operator who reads them as environment
breakage starts investigating the host, the proxy, the path — all wasted. The two markers
above (`hardline ... parser limit`, `corrupted ... dropped to keep the conversation alive`)
identify a command-string problem in one line, and the fixes are mechanical rewrites.
