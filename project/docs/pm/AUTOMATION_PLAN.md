# Local PM ↔ Hermes Automation Plan

**Status:** Design only — not activated  
**Constraint:** Roadmap order remains authoritative; one Task ID always uses one new Hermes session.

## 1. Session identity rule

- New Task ID → new Hermes session/chat.
- Correction after `CHANGES_REQUESTED` → resume the same Hermes session for that Task ID.
- `APPROVED` closes the session permanently.
- A closed session cannot receive work for the next Task ID.
- The orchestrator never combines tasks even when their write scopes overlap.

## 2. State machine

```text
PLANNED
  -> READY + session packet
  -> HERMES_RUNNING (new session)
  -> SUBMITTED
  -> PM_REVIEW
       -> APPROVED -> CLOSED -> release next task
       -> CHANGES_REQUESTED -> HERMES_RUNNING (resume same session)
       -> BLOCKED -> HUMAN_DECISION
```

## 3. Local components

```text
automation/
├── orchestrator.ps1
├── config.json
├── state.json
├── locks/
├── inbox/
├── outbox/
└── logs/
```

Responsibilities:

- `orchestrator.ps1`: validates state, launches exactly one eligible session and watches report status.
- `config.json`: repo path, Hermes command/model, timeout, spend/attempt limits and safety mode.
- `state.json`: active Task ID, task path, Hermes session ID, attempt count and last PM decision.
- `locks/`: prevents two agents from writing the same workspace concurrently.
- `inbox/outbox`: immutable prompt/result envelopes for audit.
- `logs/`: orchestrator events only; coding evidence remains in each session `LOG.md`.

## 4. Hermes invocation

Hermes is installed locally and exposes `hermes.exe`, including one-shot and resume modes. Before automation, run configuration/health checks and select an explicit provider/model.

For a new Task ID, the launcher reads only that task's `START_PROMPT.md` and starts a new Hermes session. It records the returned session ID. For corrections, it resumes only that stored ID and sends the PM correction prompt.

The launcher must never use the most-recent session implicitly because that can cross task boundaries.

## 5. PM review boundary

Recommended initial mode is semi-automatic:

1. Orchestrator launches Hermes and waits for `REPORT.md = SUBMITTED`.
2. Orchestrator stops and emits `PM_REVIEW_REQUIRED`.
3. User asks Codex PM to review the Task ID.
4. Codex inspects diff/evidence and writes `PM_REVIEW.md`.
5. If approved, Codex creates the next session packet; orchestrator may launch it only after explicit user confirmation.

This preserves the current PM quality gate. Fully unattended Codex review requires a separate supported programmatic Codex/API entrypoint and must not pretend to be this live desktop task.

## 6. Safety requirements

- One workspace lock; no concurrent Hermes coding session on the same worktree.
- Explicit Task ID and exact session path in every prompt.
- Write-scope diff audit after Hermes exits.
- Timeout, maximum three correction attempts and cost/token budget.
- Stop on `BLOCKED`, missing report, changed TASK/PM_REVIEW, destructive command or scope violation.
- No automatic commit, push, merge, deletion, migration or task approval.
- Dirty-worktree snapshot before each run; existing user changes remain protected.
- New task is never released from Hermes' own recommendation; only PM `APPROVED` releases it.

## 7. Rollout without changing the roadmap

### Phase A — Current workflow

Manual copy of `START_PROMPT.md`; PM review remains in this Codex conversation.

### Phase B — Safe launcher

Build a local launcher that performs health check, new-session enforcement, state/lock management and report watching. Test it on a documentation-only sandbox task, not a roadmap coding task.

### Phase C — Assisted corrections

Launcher can resume the same Task ID after `CHANGES_REQUESTED`, but only from a PM-authored correction envelope.

### Phase D — Optional unattended PM

Consider only after a supported Codex/API review runner is configured, budgets and destructive-action controls are proven, and at least five consecutive sessions pass scope audits. Human approval remains mandatory for schema migration, data cleanup, dependency changes and releases.

## 8. Activation prerequisites

- `hermes doctor` passes.
- Explicit Hermes provider/model works in one-shot mode.
- Session ID can be captured and resumed deterministically.
- Dry-run proves one Task ID creates exactly one new session.
- Write-scope validator detects an intentional violation.
- Lock prevents concurrent runs.
- User approves automation config and budgets.

Until these prerequisites pass, continue the existing manual start/review cycle exactly as defined in the roadmap.
