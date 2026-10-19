# S08 writer/worker model override and live steering

Use this reference when the user changes the mandated writer/worker model mid-handoff or after a packet has already been prepared.

## Trigger signal

User says something like:
- "dừng lại và nghe lệnh tôi"
- "sử dụng model deepseek v4 flash của nhà cung cấp VietAPI chạy tiếp task vừa rồi"
- "cho các writer và worker ấy"

Treat that as a **manager-level steering command** for spawned writer/worker processes, not necessarily for the current chat model. Stop launching or coding until the new routing rule is reflected in the packet/state.

## Required sequence

1. **Stop immediately**
   - Do not launch another writer while clarifying.
   - If a writer is already active, do not create a second writer. Poll/inspect the active process first, then decide whether to let it finish, kill it, or mark BLOCKED according to the user's order.

2. **Rewrite packet routing before launch**
   - Update the current task `TASK.md`, `LOG.md`, `REPORT.md`, and `output/MANAGER_STATE.md` so they name the new writer/worker model exactly.
   - Include provider and reasoning level, e.g. `deepseek-v4-flash via provider custom:vietapi, reasoning max`.
   - If an old experimental model name remains in the packet, fix it before process launch.

3. **Create/update START_PROMPT.md**
   - Put the model/provider/reasoning directive at the top.
   - Include: "Do NOT switch model/provider/fallback. If rejected, STOP with REPORT.md = BLOCKED and paste the exact error."
   - Clarify whether the override applies to all writers/workers, read-only lanes, or only the code writer. If the user says "cho các writer và worker ấy", apply it to all spawned writer/worker processes unless a later instruction narrows it.

4. **Use Hermes CLI flags explicitly**
   - Verify `hermes chat --help` supports the needed flags if uncertain.
   - Launch one-shot/background writer with explicit flags:
     ```bash
     hermes chat -q "$(cat docs/pm/sessions/<task>/START_PROMPT.md)" \
       --provider custom:vietapi \
       --model deepseek-v4-flash \
       --max-turns 500 \
       --pass-session-id \
       --accept-hooks \
       --yolo \
       --source tool
     ```
   - Use `background=true` + `notify_on_complete=true` for long writer work.

5. **Confirm real process evidence**
   - Only report "launched" after the terminal/process tool returns a real background process id/PID/session evidence.
   - Record the process id/PID in manager notes and later in the task report if relevant.

## Pitfalls

- Do not confuse the active chat model with the required writer/worker model. The chat can be on `deepseek-v4-pro` while spawned workers must use `deepseek-v4-flash`; launch flags and packet text are the source of truth for workers.
- Do not leave stale experimental model names such as Muse Spark in `TASK.md`, `LOG.md`, `REPORT.md`, or `MANAGER_STATE.md`; Codex/model-quality review will treat this as contaminated evidence.
- Do not claim the writer has started from intent alone. Process id/PID/session output is required.
- **Probe the exact provider-qualified model ID before launch.** Example C2: `muse:meta/muse-spark-1.2.-contributor` (with ".-") 404s; correct is `meta/muse-spark-1.2-contributor` via `muse` provider (config.yaml `providers.muse`). Run `hermes chat --provider muse --model "meta/muse-spark-1.2-contributor" -q "Hello"` and confirm a session returns in ~7s; if 404 `model_not_found`, STOP as BLOCKED_MODEL_ROUTE.
- **Delegate lanes inherit the manager chat's model** — a manager on `custom:meta-ai` (pay-as-you-go, số dư 2425) will spawn reviewers that also hit `meta-ai` and 403, even though the writer correctly uses `muse` via 9Router local. Either pin reviewers to the local 9Router (`--provider muse --model meta/muse-spark-1.2-contributor`) or do not use `delegate_task` for this project — have the manager do the read-only audit inline.
