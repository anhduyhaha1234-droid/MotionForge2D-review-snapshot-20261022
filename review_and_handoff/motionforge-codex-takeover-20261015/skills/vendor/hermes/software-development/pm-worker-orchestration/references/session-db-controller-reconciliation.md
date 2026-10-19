# Reconciling the ACTUAL controller from the Hermes state.db (measured 2026-10-11)

Situation: the run registry named Manager SID A, but the rounds were actually driven by
a different, newer Manager chat SID B that the user had opened for a correction round
("registered manager is stale; actual controller differs"). Proving the chain — and
identifying your OWN session id when you resume as the next Manager — is read-only DB
work.

## DB facts (this Hermes build)
- DB: `C:/Users/Admin/AppData/Local/hermes/state.db`. Open read-only:
  `sqlite3.connect(f"file:{DB}?mode=ro", uri=True)` + `PRAGMA query_only=ON`.
- `sessions` columns include id, source, started_at, ended_at (epoch floats),
  message_count, tool_call_count, title, parent_session_id, cwd. There is NO
  created_at/updated_at column; `ended_at` stays NULL for idle-but-never-finalized
  sessions — NULL is NOT liveness.
- `messages` timestamp column is named **timestamp** (not created_at). Per-session
  last activity = MAX(messages.timestamp); active vs compacted = the `active` flag.

## Find your OWN session id
Search the messages table for a unique marker from the prompt the user just pasted,
newest first, preferring role='user':
`SELECT session_id, id, role, timestamp FROM messages WHERE content LIKE '%<marker>%' ORDER BY id DESC LIMIT 10`.
Tool RESULTS also echo the prompt text, so take the newest USER-role match as the
session being served; cross-check the sessions row (started_at ≈ now).

## Prove the actual controller chain
- For each candidate SID: first user message (provenance — e.g. the packet's first
  line), last message tail, MAX(timestamp), and whether its messages reference the
  dispatch artifacts (packet names, launch logs).
- The session that WROTE the round packet / ran the launcher is the ACTUAL controller
  (found by `content LIKE '%<packet name>%'` hitting a tool call that wrote that packet).
- Record the whole chain in the takeover/reconcile evidence: initial manager →
  registered-manager takeover → actual correction controller → current manager, each
  with last activity + status. Update the run registry in place ONLY with a byte
  preimage kept (registry may be CRLF; write preserving CRLF, verify json parses).

## Zero-writer proof (before patching harness or resuming a worker)
Three independent legs, all cheap:
1. Process scan: no worker/controller/launcher pids alive (identity-checked;
   monitors/heartbeats are not writers of the worker tree).
2. Disk: newest mtime under the worker tree predates the last terminal by hours/days
   (walk + getmtime with an explicit cutoff epoch — do not trust `find -newermt` under
   git-bash, it is timezone-shifted).
3. Queue/resource: render queue empty.
State the gate explicitly in evidence (e.g. CLEAR_TO_PATCH_AND_RESUME_SAME_OWNER).

## Resume-vs-transfer decision
Counts alone (active/compacted messages) never justify an owner transfer. Check the
last close-out message for coherence and explicit next actions; on a clean close-out
resume the exact SID with a compact packet that restates the current contract.
Transient infra text in the log (e.g. "API call failed after 3 retries") is a
reconciliation input, not a terminal state.
