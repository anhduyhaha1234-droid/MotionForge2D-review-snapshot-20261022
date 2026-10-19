# MF-END-12 round — evidence-manifest & guard lessons (2026-09-28)

Measured on one round (role/prop source tracks, real SAM2.1 run). Five failures worth
re-using as checks:

1. **A manifest refreshed inside the gate goes stale on the gate's OWN ledger row.**
   `final_gate.py` appended its `commands.jsonl` row via an outer `logcmd` wrapper
   (which writes AFTER the command exits), then refreshed `evidence_manifest.json`
   inside the same run → the manifest's recorded sha of `commands.jsonl` was one row
   behind. Fix: the gate appends its own ledger row FIRST (measuring its own
   start/end), THEN refreshes the manifest, and strips its own earlier duplicate row
   by label while saying so in the row's `note`. Verify end-to-end: re-hash every
   file the manifest lists and assert 0 mismatches (a blanket mismatch = bug signal).

2. **Protected-drift guards must compare BLOB ids, never worktree bytes.**
   `sha256(worktree file) == sha256(git show HEAD:path)` reported drift for 7/7
   protected files (100% failure = bug signal) because `core.autocrlf=true` checks
   the same blob out as CRLF. Use `git hash-object <path>` vs `git rev-parse
   HEAD:<path>` plus `git diff --name-only HEAD -- <path>`; both must agree.

3. **A 64-hex pin copied by eye loses a character and the assert that catches it
   must exist.** A source-window sha was transcribed as `…20b096b4…` instead of
   `…20b0962b4…` in BOTH the harness and the test; only the harness's
   `sha_matches_pin` assertion fired. Always re-read the pin from the manifest file
   programmatically, and keep the assert in the runner, not just in review.

4. **CI occlusion fixtures: place the occluder by FIXED coordinates, not per-frame
   relative offsets.** An occluder drawn at `x-8 .. x+26` followed the target, so a
   narrow second object (a prop) fell out of the occluder's shadow two frames early
   and the engine (correctly) classified `out_of_frame` instead of `occluded`.
   A stationary bar covering all frames' positions gives the intended
   `occlusion_run` for every target.

5. **The cheap capability probe is a real probe — use it as the artifact's engine
   evidence.** `Sam2ExtractionProvider.capability_report()` (stat + PK magic + package
   import + torch backend) cost ~0.3 s and let the sealed artifact carry
   `probe {status: AVAILABLE_PROBED, checkpoint, bytes, device}`; the production gate
   then refuses any artifact whose probe is missing or not ready, and an unprobed
   engine (SAM3 without weights) is refused with its own typed code.

Also reused from earlier rounds: MSYS `/c/...` paths break `ffmpeg`/`python.exe`
(pass `C:/...`); `python -B` + `PYTHONDONTWRITEBYTECODE=1` keeps `__pycache__` out of
writers' trees; `git commit` can print `fatal: bad object refs/...` +
`error: failed to perform geometric repack` (auto-gc on a pre-existing broken ref)
and still succeed — confirm with `rev-parse HEAD/HEAD^` and disclose.
