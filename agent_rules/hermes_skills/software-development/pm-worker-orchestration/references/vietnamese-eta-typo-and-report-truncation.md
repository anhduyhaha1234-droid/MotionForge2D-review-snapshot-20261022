# Vietnamese Typo ETAs & Live-Traffic Signals (verified 28/08 via S10)

## Typo / no-diacritic variants that still mean ETA (go+ETA co-occurrence)

- `essti,at` — often co-occur in one message (`essti,at baoh xong`). Both are typos/shorthands for `estimate` / `ETA`.
  - `essti` / `esti` / `es ti` — all map to `estimate`.
  - `at` — standalone `at` in this context is ETA shorthand, not English preposition.
  - `baoh` / `bao` — no-diacritic for `báo` (as in `baoh xong` = `báo xong` = report done).
  - `up darte` / `updarte` / `up-date` / `up darte tiến độ đi` — all map to `update`/`up date`.
- All variants trigger the same rule as canonical `estimate` / `bao gio xong`: instant date-anchored wall table (ideal vs +1 correction) co-located with dispatch confirmation, not deferred to heartbeat. Run `date` first.
- Normalization before intent matching: strip diacritics, allow truncated/typo variants, do not treat `up darte` or `essti` as unrelated free text.

## Liveness check typo

- `sao lại dừng r` — truncated typo for `sao lại dừng rồi?` / `sao thấy dừng rồi?`. Means "why did it stop?" — a liveness heartbeat check, not ETA, but also requires instant `lead-with-status` reply (what is RUNNING / RUNNING_RETRY_WAIT / waiting-for-join, not silence). In S10-C1 this co-occurred with `Network connection lost` ×3 retries on `T01C-C3` (RUNNING_RETRY_WAIT 5 min, same owner, unbounded until success).

## Report truncation pitfall (S10 exit 04:12 28/08)

- `docs/pm/sprints/S10-SPRINT_REPORT.md` was written via inline shell heredoc `cat > ... <<'EOF'` containing JSON/dict literals with `{` and quotes — bash reported `unexpected EOF` / `syntax error near '{'` / `unexpected end of file from {'` and truncated the file at 73 lines, before the evidence table. Fix: use `execute_code` file-write (`Path.write_text`) for any report that contains JSON/brace-heavy content, not a shell heredoc. Re-verify with `wc -l` + `tail` after every report write; a truncated report breaks the review packet skeleton and must be rewritten via file-write, not patched.
