# The transport-flap resume cycle (lane died on 502/503, not on work)

Measured 2026-09-24 on a 3-lane round against a local router that fronts an upstream provider.
Two lanes died mid-run on the same day; a second lane died again *during its own resume*. This is
the loop that keeps a round moving without ever mistaking a flap for a result.

## 1. Recognise a flap from the log SIZE, not the exit code

| log bytes | tail content | what it is |
|---|---|---|
| ~124–125 B | `API call failed after 3 retries: HTTP 503: [… ] [502]: fetch connect timeout (reset after Ns)` | pure **transport flap** — the run returned `exit 0` having done nothing more |
| 6–10 KB | the worker's own closing report / remaining-itinerary | worker **stopped on turn budget** (see `monitoring-and-finish-runs.md`) |

Both return `exit 0`. The discriminator is the *size and shape of the payload*. A launcher that
gates on the exit code reports both as "done normally" and the round silently loses work.

## 2. State, not silence

A flap is `RUNNING_RETRY_WAIT` — **never** `TASK_SUBMITTED`, never a blocker. Report the incident
immediately (it is a liveness event), naming: the remaining uncommitted paths, the evidence files
already written, and the scheduled retry time.

## 3. Wait ≥5 minutes, and ENCODE the wait in the launch command

The canonical policy is "wait ≥ 5 minutes, then resume the **same** owner with the same provider /
model / scope". Do not hold that wait in your head across turns:

```bash
# background launch: the sleep is part of the command, so the retry cannot fire early
sleep 300 && python tools/append_dispatch.py <task> <round> <packet> <parent> … \
           && python tools/mfv1_launch.py <packet> <tree> <log> <receipt> --resume <session>
```

Measured schedule that worked: flap at 13:47:46Z → resume dispatched with `sleep 280` (fires
13:53Z); a second lane staggered 45 s behind it. Stagger stays in force even after a flap.

## 4. Measure what the resume actually wrote before assessing loss

A resume can flap again and write **nothing**. Distinguish the two by artifact mtimes against the
resume's own start time, not by assumption:

- `S12QA` resume: evidence written 13:31–13:43Z and **3 uncommitted in-allowlist paths** ⇒ partial
  progress, resume must continue from its own leftovers (tell it to re-read its own scripts and
  preimage JSONs and state what was already done vs still open).
- `BENCH` resume: **no file under the evidence root had an mtime after the resume started** ⇒ the
  attempt is a no-op; the correct move is to re-dispatch the *same* packet under a new round label
  (`…-resume-after-502-b`), not to write a new one or to attribute progress to it.

## 5. Give every resume its own packet, round label and ledger row

Reusing a packet file name for a second attempt makes the provenance resolver ambiguous. Emit a new
round label each cycle (`resume-after-502`, `resume-after-502-b`), and after the run starts resolve
the **new minted session id** and refresh the watchdog's session/pid sets (a stale set makes the
fresh lane invisible — see `monitoring-and-finish-runs.md`).

## 6. When flaps repeat, reduce concurrency and say why

A flap is upstream-side evidence, not a worker verdict, so the retry loop continues indefinitely —
but if flaps repeat with the stream count at its cap, drop one stream and disclose the reason with
the flap timestamps. An unexplained concurrency change is as bad as an unexplained retry.
