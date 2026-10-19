# S12-C1 W2/W3: fragment-reply liveness + hermes-CLI native-path rule (2026-09-08)

Two small patterns from the S12-C1 correction wave (T02 fix-commit, INT01 W2-fix
merge, T03B W3 dispatch). Complements (does not replace) the stall rules in
SKILL.md ("log growth without tip movement", "first stall-suspect nudge demands
bytes") and `references/s12c1-preflight-session-identity-gate.md`.

## 1. Truncated-fragment replies are failed delivery, not answers

Observed: exact owner T03B (`20260907_125027_0c90f3`, session ALIVE, worktree
frozen at old tip `6297869`, porcelain 0) returned two consecutive sub-sentence
fragments across dispatch + nudge (`"3–C14 ngay."`, `"R fetch reality before
deciding to code."`) — cut off mid-sentence, no RULES_LOADED, no tip/porcelain
movement, no evidence bytes.

- Diagnose as TRUNCATED DELIVERY, not a status report and not (yet) a
  context-health failure: session alive + zero state advance + fragment shape.
- Next nudge must be SHORT: demand only tip + porcelain + read-only fetch
  result. Do NOT re-send the full correction prompt in the same turn — long
  prompts to an already-struggling worker raise truncation risk and burn a
  full cycle for another fragment.
- Escalation unchanged and still tip/porcelain-based: 2 consecutive nudges
  with zero tip/porcelain/log advance ⇒ freeze + BLOCKED_CONTEXT_HEALTH /
  OWNER_TRANSFER_REQUIRED evidence. Fragments never count as progress.
- Mirror case (same wave): T02 fix-commit wrapper returned bare
  `"Terminal hiccup"` twice with zero state change, then succeeded on an
  identical same-owner retry (`81793a8`, 35 passed + 1 skipped). Transient
  trailer + no tip movement ⇒ retry the SAME owner once; re-scope only when
  the retry also yields zero advance. Verify tip/porcelain before judging
  either direction.

## 2. hermes CLI file args need Windows-native paths

- `hermes sessions export --format jsonl --session-id <sid> -` (stdout via
  `-`) returned 1 unparseable line — not a usable transcript path.
- File export to an MSYS-style path (`/c/Users/.../Temp/t03b_export.jsonl`)
  died inside the CLI's own `open()` with `FileNotFoundError`: the hermes CLI
  is a Windows binary and resolves paths natively, exactly like node/python
  (cf. terminal-engineering-discipline pitfall on MSYS-vs-native paths).
- Rule: every hermes CLI file argument (export output, prompt files, logs)
  uses native `C:/Users/...` form, never `/c/...`. Same duality, one rule.

Pointer request for curator: add one line under the Manager skill's
monitoring/liveness section referencing this file
(`references/s12c1-w2w3-liveness-and-cli-path.md`). Direct SKILL.md patch
avoided (100KB file, prior read-before-write refusal on record).
