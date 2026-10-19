# Sequencing: live writers during verification; provider payload flaps (2026-09-28, MotionForge delivery)

## 1. Never run a read-only verifier while a writer is live on the same tree

Measured: an independent BENCH verification ran while a repair writer was mid-flight on the same proof
root. The verifier itself recorded the consequences (its finding F1 "proof root has a live writer"):

* 1 of 247 hash checks became **UNVERIFIABLE-NOW**: `user/comfyui.db.lock` was held with an exclusive
  lock by the live server, so it could not be hashed at audit time (it had hashed clean in two earlier
  reads). That is a THIRD outcome, distinct from MATCH and MISMATCH — record it as unverifiable, with
  the reason and the holder's pid/epoch; never fold it into either column.
* Any "frozen snapshot" claim becomes time-bound: state the audit window and which paths were still
  being written when the audit ran.

Rule: sequence verification AFTER every writer on that tree has exited, and capture writer quiescence
as evidence (receipt exit + pid gone + two identical tree listings ≥60 s apart). If concurrency is
unavoidable, scope the verify to files no writer holds and say so in the verdict line.

## 2. Long-run workers can die at the LAST step from provider payload flaps — the work is not lost

Measured twice on one lane: the provider returned `422 … messages.NNN.tool.content.str` (then
`502 ERR_HTTP2_STREAM_ERROR`) AFTER all GPU work completed but BEFORE the docs were written. The
worker session died at the final report step; the deliverables were simply absent (report size
unchanged, candidate doc missing) while every artifact existed on disk.

Recovery pattern (used successfully, third attempt finished in 4 minutes):

1. Read the log tail and classify: "died before the work" vs "died after the work, before
   documentation". If outputs exist on disk, do NOT re-run the work — resume the same session with a
   short DOCS-ONLY finishing packet.
2. Wait ≥5 minutes (transient-connection class) before resuming; keep the SAME session / model /
   scope — never switch models because of a flap.
3. Prevent recurrence in the packet text: forbid oversized tool payloads — "write files via script,
   print ≤200-char confirmations, do not `cat` large files". The 422 named the culprit field
   (`messages.<n>.tool.content.str` = oversized tool message body).
4. After resume, verify DELIVERABLES ON DISK (sizes, shas, row counts) — exit code 0 with an empty
   docs set is the exact failure mode here. Also keep an append-only proof ledger row per phase so a
   later audit can see which phase completed vs which never landed.
