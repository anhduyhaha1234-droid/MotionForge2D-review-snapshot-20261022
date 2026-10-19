# Never dry-run a dispatcher against the real PATH

Incident (verbatim, 2026-10-06): a Manager verified a *policy patch* to its own
launcher (`dispatch_long.py`) by "testing" it with a fake child — a
`hermes.cmd` shim placed on `PATH` that was supposed to echo the argv and exit 0.
It did NOT intercept: the launcher's `subprocess.Popen(["hermes", ...])` resolved
the **real** `hermes` CLI (the `.exe` won the Windows resolution order over the
`.cmd`), which then **resumed a live production worker session**
(`--resume <real_owner_sid>`) with a throwaway test packet and ran for ~52 s.

Damage report (why it was survivable but must never be repeated):
- It wrote real files into the production output tree (`work/grid2/*`, 29 frames).
- The launcher's dispatch ledger in the *temp* root was never written (it opened
  after the child), so the temp root looked pristine — masking what happened.
- The **real** RUN ledger was untouched only because the real launcher path was
  never invoked; the hijack happened at the child level.
- No duplicate owner, no code/clip mutation — but a real owner session consumed
  turns on a nonsense prompt and the user's worker lineage got an extra user msg.

## Rules

1. **Test a launcher with a shim that CANNOT resolve to the real binary.** Do not
   rely on `PATH` precedence — on Windows `.exe` beats `.cmd`/`.bat` and the
   interpreter may still find the installed `hermes.exe`. Instead:
   - point the launcher at an explicit non-resolving command name for the test
     (e.g. `FAKE_AGENT_BIN` env var the launcher honours), OR
   - stub `subprocess.Popen` in-process (import the module, monkeypatch Popen,
     assert the argv) — this never spawns anything.
2. **Never pass a real `--resume <sid>` (or any real id) to a test invocation.**
   Use a sentinel sid that cannot exist. If the test *could* reach a real session,
   the test is unsafe by construction.
3. **Verify the shim actually fired** before trusting the test: assert a sentinel
   line from the shim appears in the log (`echo FAKE_HERMES_ARGS`). If the log's
   first line is the real CLI banner (`Initializing agent... / Resumed session
   <sid>`), the shim was bypassed.
4. **Prefer in-process argv assertion over any spawn** when the thing under test
   is command construction + argument shape (which is 90 % of launcher patches).
5. **After ANY test that could have spawned, sweep for strays** before moving on:
   `tasklist` for the child name, then walk the production tree comparing
   `os.path.getmtime` against a cut-off epoch captured *just before* the test
   (MSYS `find -newermt` is TZ-shifted — compare epochs, not `-newermt`). Delete
   the temp root and record an `incident_note` row in the real ledger.

## Incidental lesson (epoch cut-off, not `find -newermt`)

To answer "what changed in the production tree since HH:MM?", do NOT use
`find -newermt "YYYY-MM-DD HH:MM"` under MSYS/git-bash (timezone-shifted). Use a
Python walk: `os.path.getmtime(p) > cutoff_epoch` where `cutoff_epoch =
datetime(..., tzinfo=utc).timestamp()`, and print the epoch so the check is
auditable.
