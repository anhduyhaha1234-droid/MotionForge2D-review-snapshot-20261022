# S12-C1 24/24 watch loop + W3 START decision (2026-09-08)

Session: S12-C1 correction, canonical `codex/s12-integration`, C1 root
`MotionForge2D-evidence/s12/20260907-182016-C1/`.

## Explicit 24/24 order overrides prior no-surveillance

Packet §7 banned quota-consuming surveillance; user then ordered `chạy 24/24 đi`.
Standing rule applied: an explicit user 24/24 order wins over the packet's ban,
runs until an explicit user stop, authorization + stop condition recorded in evidence.

## watch_24.sh shape (bash bg loop, no cron — gateway off)

```bash
while true; do
  # read-only, zero model calls:
  CHEAD=$(cd "$CAN" && git rev-parse HEAD)
  CPORC=$(cd "$CAN" && git status --porcelain=v1 -uall | wc -l)
  AB=$(cd "$CAN" && git rev-list --left-right --count HEAD...origin/codex/s12-integration)
  TIP=$(cd "$TASK_WT" && git log --oneline -1)
  TPORC=$(cd "$TASK_WT" && git status --porcelain=v1 -uall | wc -l)
  LEDN=$(wc -l < "$C1/commands.jsonl")
  echo "[$UTC] HEAD=... porc=.. ab=[..] TASK=[..] tporc=.. ledger=.." >> watch_24.log
  # stall = tip frozen AND newest lane-log age > NUDGE_GAP (900s):
  #   -> hermes chat -q "<short stall-nudge>" -r <EXACT-owner-sid> -m <model> --provider <prov> -Q
  # task commit prints PROGRESS_* marker -> terminal watch_patterns notifies instantly
  sleep 300
done
```

Notes: `git -C /c/abs` falsely errors under MSYS bash — always `cd` first.
Nudge cadence 15 min (not 5) to protect quota; checks every 5 min are free.
Kill the loop at sprint submit; never leave it running past terminal state.

## Fetch-blocked-but-ls-remote-OK START (second instance of the stray-refs class)

`git fetch origin codex/s12-integration` died:
`fatal: bad object refs/codex/turn-diffs/captures/.../base` /
`did not send all necessary objects`, while
`git ls-remote --heads origin codex/s12-integration` == local HEAD `46feca4`
(ahead/behind `0 0`, porcelain 0). Decision: remote object-store defect, NOT a
stale base — interfaces already aligned read-only (W2 corrections disjoint from
T03B scope), so Manager posted formal START and the lane coded immediately,
still banned from merge/rebase. Fetch error alone never blocks a DAG-ready lane.

## Truncated worker replies (transport loss, not answers)

Two consecutive T03B replies arrived as fragments (`3–C14 ngay.`,
`R fetch reality before deciding to code.`) with correct session_id trailers;
session was alive (`just now`), WT clean at `6297869`. Recovery: re-nudge
demanding the FULL answer in one reply (RULES_LOADED + tip + porcelain + fetch
result + scope + first test + ETA). Third reply came back complete with real
evidence (tip, porcelain 0, ls-remote == `46feca4`, prompt rows read, ETA
60–90 min). Rule: never treat a fragment as a status verdict or stall evidence
— stall judgment stays on tip + porcelain, never on reply length.
