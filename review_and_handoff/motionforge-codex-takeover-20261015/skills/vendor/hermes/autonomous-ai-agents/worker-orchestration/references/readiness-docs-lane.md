# Readiness Docs-Only Lane — S11-P02 Pattern (2026-08-23)

Post-sprint, pre-dependency-exit planning packet: N read-only audit lanes in
parallel + one synthesis lane. Zero production writes. Proven on S11-P02A/B/C/D
(A QC domain/dependency audit, B checks/harness inventory, C Review-Queue
UX/API gap audit, D T02..T06 synthesis) — all four first-try TASK_SUBMITTED,
manager-verified same day.

## Wave structure

- **Wave 0**: preflight — rules file re-read (mandatory per parent prompt),
  HEAD/branch/dirty-count snapshot, DB env UNSET check, model-route liveness,
  worker/ffmpeg process scan, protected-hash baseline of prior sprint outputs.
- **Wave 1**: A∥B∥C simultaneously. All three are read-everything /
  write-own-dir-only; write-sets are disjoint by construction
  (`output/<run>/lane-{a,b,c}/**`). Safe to parallelize even on the shared
  provider because they are short and mostly local reads.
- **Gate between waves**: manager spot-checks each lane's claims against real
  code (grep the cited symbols yourself) BEFORE dispatching D.
- **Wave 2**: D synthesis, NEW session, reads lane outputs + roadmap +
  handoff docs only.

## Per-lane prompt skeleton (what made it land first-try)

1. Role + extreme write discipline: "chỉ được GHI vào <lane dir>/**;
   READ-ONLY toàn bộ phần còn lại" with explicit forbidden list
   (app/** tests/** frontend/** migrations/** docs/pm/** data/fixtures MAIN
   prior outputs), no network/model downloads, no commit/push.
2. Context: current sprint states verbatim (which sprints APPROVED, which
   BLOCKED_DEPENDENCY, what exists from earlier rounds).
3. Deliverables: exact .md filenames with a one-line spec for each.
4. Claim gate: "mọi claim file:symbol tự verify bằng grep/read trước khi ghi;
   self-check VERIFIED/UNVERIFIED từng claim".
5. Vocabulary: REPORT.md ends TASK_SUBMITTED; never self-APPROVED.

## Synthesis (D) prompt requirements

- Enumerate exact input files (every lane deliverable by path).
- Demand: session-sized IDs each with outcome / depends-on / exclusive
  write-set / forbidden paths / tests / session rule / binary acceptance.
- Flat DAG + explicit parallel-safe pairs + serialize-pairs naming shared files.
- Migration rule: `alembic heads` measured AT RUN TIME as down_revision —
  never hard-coded (baseline moves between runs).
- Every production ID labeled BLOCKED_ON_<gate> with gate-open conditions.
- MEASURED / PROPOSED / UNKNOWN split; UNKNOWN items name who decides (Codex).
- Trace matrix: every output section cites lane-A/B/C section + roadmap row.

## Moving-baseline traps

- A parallel production sprint (S09-T00-I01/I04 here) can mutate models.py,
  schemas, migrations DURING your readiness run. Rules:
  - Docs anchor to SYMBOL NAMES (`grep class StructuralLockManifest`), never
    line numbers or hashes for anything outside your lane's frozen outputs.
  - Cross-lane attribution: verify via wmic/psutil cmdline + mtime windows +
    state.db message timestamps that YOUR lanes didn't write it; record in the
    coordination report as cross-lane activity, NOT your lane's violation.
  - Synthesis re-verifies symbols itself at write time and records the delta
    ("lane-A said missing at 13:45, now exists at 15:33") as MEASURED update.
- Prompt-supplied numbers: if a lane cannot find evidence for a number in the
  prompt (e.g. "suite took 237s"), it must record UNVERIFIED + its own
  measurement instead of echoing it. Manager independently re-measures to
  adjudicate (here: 64 collected confirmed; the 237s stayed unverified).

## Manager verification checklist per lane

1. Deliverable manifest present (all named .md exist).
2. Spot-check 3–5 strongest claims against real code (grep symbol → line).
3. Self-check honesty markers: VERIFIED/UNVERIFIED table populated; grep for
   self-APPROVED = zero (allow quoted external states).
4. Write-set audit: git status unchanged outside output dirs (+ known
   parallel-lane edits attributed).
5. For D additionally: all IDs enumerated, trace matrix rows resolve, DAG has
   no cycle, parallel pairs' write-sets genuinely disjoint, gate labels present.

## Terminal state

`S11-P02 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`; documented
production tasks stay `BLOCKED_DEPENDENCY_ON_<gate>`. Write ONE coordination
report (waves, sessions, verification evidence, moving-baseline notes,
protected hashes after-run). Lane stops — planning packets NEVER open the
gate they document; production waits on the external dependency exit +
reviewer approval.

## Process-tracker anomalies at closeout

- `process poll/wait` → `not_found` after an orphan-recovery marker does NOT
  mean the worker died mid-flight: lane C had written all 4 deliverables
  before the tracker lost the id. Ground truth = tee'd log exit banner +
  artifact mtimes + REPORT verdict. Never relaunch off tracker absence alone.
- Identical wait payloads across polls = polling blind; read raw log tail +
  state.db last-message timestamp instead.
- psutil scans: wrap per-process access in try/except (processes die
  mid-iteration → KeyError 'pid'), filter by process-name prefix BEFORE
  touching cmdline, and beware a grep pattern matching its own python -c
  cmdline — heredoc scripts + two-pass confirmation beat clever one-liners.

## Correction round on the PLAN itself (C1 pattern, 2026-08-23)

Codex can CHANGES_REQUESTED the synthesis packet (not code). Proven round:
S11-P02D-C1 — resume the SAME synthesis owner session, route unchanged,
worker write allowlist narrows to ONLY the plan + REPORT files; manager
may append to COORDINATION_REPORT.md only.

Before dispatching the correction:

- Hash-baseline EVERY prior output (all lane .md files + both synthesis
  files + protected production hashes like T01 engine/handler) — the
  post-exit hash diff is the only-allowlist-changed proof.
- Check owner liveness via state.db last-message timestamp; resume beats
  recovery (recovery needs death evidence).

Dispatch prompt structure that landed first-try (~40 min end-to-end):

- Findings verbatim (F1..Fn with P-levels).
- Frozen BA/CODEX decisions relayed VERBATIM as binding (decisions A–H
  here) — worker APPLIES them consistently across every ID, never
  re-decides.
- The EXACT target decomposition pre-named by Codex (here: 17 IDs each
  with one-line scope) — worker writes it up, never invents the split.
- The exact wave DAG incl. the parallel-evidence requirement per pair.
- Shared-file ownership table requirement: ONE named owner per shared
  file; "Manager resolves merge conflicts" is NOT legitimate write-set
  design.
- An explicit "manager will verify" acceptance list so the worker can
  self-check before TASK_SUBMITTED (it did — REPORT carried a full
  findings→fixes table + self-check rows).

Post-exit manager gate battery (STRUCTURAL greps on the plan text):

- Count IDs (`grep -c '^### W'`) == expected N; each ID appears once.
- Per-ID field completeness: sample ≥3 IDs × 8 required fields.
- Allowlist closure: every test path an ID REQUIRES sits INSIDE that ID's
  write-set (catch #1 from Codex: "add these tests" + "forbid everything
  outside allowlist" = impossible task).
- Mandated coverage: overlay/roadmap-mandated enumerations (8 QC reason
  codes) appear in outcome AND binary acceptance; grep
  `<mandated-item>.{0,40}UNKNOWN` = zero.
- Negative greps: no arbitrary-create POST for domain objects (creation
  via internal repository/service only; tests seed via repository
  fixture), no explicit-acceptance/dismiss-to-pass control anywhere,
  §UNKNOWN contains only measured-runtime unknowns (exit timing, perf)
  — never product decisions.
- Dependency sanity: no parallel pair where one consumes the other's
  still-unfreezing contract; golden-manifest tasks wait until BOTH the
  policy producer AND detector set are MANAGER_VERIFIED.
- Monolith check: policy+runner+registry = one ID max; detectors batched
  2–3 per ID; orchestrator alone; UI alone; each server-owned action
  route alone.
- Protected state: lane outputs byte-identical to baseline hashes,
  HEAD/branch unchanged, prior-sprint hashes intact.

Plan-quality gates worth applying BEFORE first submission (each maps 1:1
to a finding Codex returned — checking these pre-flight would have saved
the whole round): AC→allowlist closure per ID; mandated enumerations
exhaustive and assigned to concrete IDs (never droppable); one-session
sizing per ID; parallel pairs consume only FROZEN inputs; every product
decision either frozen-by-prompt or explicitly UNKNOWN-with-decider.

## Correction round TWO on the PLAN (C2 pattern, 2026-08-23)

Second CHANGES_REQUESTED against the synthesis packet. Same owner-session
resume discipline as C1, plus three upgrades:

### Preflight upgrade: reconcile against the REVIEWER's recorded hashes

C1 baselined your own outputs; C2's verdict records the hashes CODEX saw
(PLAN `20eb80dc…34ab0`, REPORT `f43c4012…a8fbb`). Preflight now has three
steps: (a) sha256 your current artifacts and require an EXACT match with
the reviewer-recorded pair — a match proves zero writes since review;
(b) re-hash after ≥2 s and diff — byte-stability proof against a writer
that died between snapshots; (c) any mismatch ⇒ `BLOCKED_CONCURRENT_
WRITER`, do not dispatch. Keep the lane A/B/C + prior-sprint protected
hashes in the same snapshot for the post-exit only-allowlist-changed diff.

### Findings freeze at a LOWER granularity than C1

C1 froze decisions and the ID decomposition; C2 freezes EXACT artifacts:
per-task literal write-set enumerations (T04D = 11 named paths, T05B = 7,
T06A = 7 media_manifests, T06B = 5 golden_manifests), a fixed migration
filename + revision ID (`e11a02a2026f_...py`; down_revision still resolved
from live single head at activation, multi-head ⇒ BLOCKED_MULTI_HEAD),
lifecycle invariants verbatim (NO_AUDIO_PRESENT ⇒ `not_applicable` result +
ZERO QCItems; `audio_missing` QCItem only when source HAS audio but output
lost it ⇒ blocker/open; delete every `resolved-at-create` mention), and a
one-line future-code change quoted exactly (`FUTURE_CAPABILITY_BLOCKERS
["review_work"] = None`). Relay each finding with its literal strings;
the worker applies them mechanically instead of interpreting prose.

### Post-exit gate battery additions

- Per-ID field completeness by SCRIPT over ALL blocks, never samples:
  split on task headings, assert all 8 required field markers in every
  block (17/17 here). Sampling missed nothing at C1 but C2's prompt made
  exhaustiveness an explicit acceptance item.
- Exact-enumeration counts: extract each ID's write-set section (up to
  its `**Forbidden` marker) and count backtick-quoted paths / manifest
  names — must equal the prompt's numbers exactly (11/7/7/5).
- Glob-residue trap: a naive `\*\*` grep FALSE-POSITIVES on markdown bold
  markers (`**Outcome**`) — six bold fields per block look like six globs.
  Real source/test globs are patterns like `<dir>/**`, `*.json`, `*.tsx`
  inside the write-set lines; regex accordingly (`[\w\-]+/\*\*|\*\.json|
  \*\.tsx`), or you'll accuse clean blocks.
- Stale-string battery grows each round: previous round's banned phrases
  stay in the grep list forever (`resolved-at-create`, `<new_rev>`,
  "nếu Codex muốn", "chọn phương án", the old flip-prose arrow string) —
  regression protection for the plan text itself.
- Only-allowlist-changed proof: hash-snapshot ALL lane+synthesis .md files
  before dispatch and after exit; the diff must show exactly 2×N lines
  (N changed files × old+new), everything else byte-identical.

Worker-side behavior worth keeping in packets: the resumed writer ran its
OWN final-gate script mid-run, found its own leftovers (one surviving
`resolved-at-create`, `*.json` shorthand in the shared-files matrix), and
cleaned them BEFORE TASK_SUBMITTED — the explicit "manager will verify"
acceptance list is what powers that self-check. Expect ~50–60 min wall
time for a full-plan rewrite of this size on alpha/max.

## Correction round THREE on the PLAN (C3 pattern, 2026-08-23)

Third CHANGES_REQUESTED against the synthesis packet (S11-P02D-C3: findings
C3-F1 serialize fixture builders BEFORE threshold freeze — old `W3 T03A ∥
T06A` banned as read-after-write; C3-F2 audit metadata — title/current-Task
field must name REV 4 / `S11-P02D-C3`). Same owner-session resume +
hash-baseline discipline as C1/C2, plus four new lessons:

### Finding types shift from CONTENT to STRUCTURE + METADATA

- C1 froze decisions; C2 froze exact artifacts; C3 froze the DEPENDENCY
  ORDER itself: a full re-serialization into a 12-wave binding DAG with
  T06A physically moved BEFORE T03A (the policy consumer now waits for the
  fixture producer). The worker reordered the whole block in the document,
  relabeled all 17 heading waves, updated Depends-on lines, parallel-pair
  summary, ownership matrix, and trace/self-check — enumerate ALL of these
  touchpoints in the dispatch prompt or some stay stale.
- Audit metadata is a first-class finding: reviewer greps TITLE + current
  Task field FIRST. A correct plan with a stale `REV 3 / C2` header still
  returns CHANGES_REQUESTED. History line keeps every prior rev (REV1
  initial → C1 → C2 → C3-current); historical mentions are allowed ONLY in
  history/report prose.

### Regression guards ACCUMULATE across rounds

Each correction prompt re-lists the previous rounds' closures as explicit
REGRESSION GUARDS ("C2-F1..F4 must stay closed"), and the manager's
post-exit grep battery grows monotonically — the stale-string list never
shrinks (`resolved-at-create`, `<new_rev>`, banned open-choice phrases,
old flip-prose arrow string, plus each round's additions). Re-grep the
FULL cumulative list every round; that IS the regression proof for the
plan text.

### Verification-script fragility (three traps hit in one gate battery)

- HEADING FORMAT DRIFTS between revisions: the worker renamed
  `### W1 · S11-T02A — …` to `### W1 · T02A — …`. A verification regex
  written against LAST round's heading shape silently matches ZERO blocks,
  and every downstream completeness check then vacuously "passes"
  (`all([]) == True`). Always grep the live headings FIRST, build the
  splitter from what is actually there, and treat "0 blocks parsed" as a
  SCRIPT BUG, never as evidence.
- The `·` middot in headings defeats naive `re.split(r'(?=### W\d+ · S11-T)')
  patterns under mixed encodings. Split on `^### ` LINES
  (`re.finditer(r'^### .*$', plan, re.M)`), then classify each heading by
  content (`re.search(r'W\d+\s*·\s*T\d+[A-F]', h)`).
- FALSE-POSITIVE parallel-dependency flags: extracting `T\d+[A-F]` refs
  from Depends-on lines flagged `T04A depends-on same-wave T06B` — but the
  actual line reads `(+ T06B không ràng buộc)` ("not a constraint"): the ID
  is cited specifically to DENY dependence. Same-wave CITATION ≠ same-wave
  DEPENDENCY; read the sentence before ruling a violation, and record the
  false-positive dismissal (with quote) in the verification table.

### Cycle/ordering proof by script

Extract per-ID Depends-on edges → DFS topological sort for acyclicity →
assert every edge points to a STRICTLY EARLIER wave (strictness is what
proves serialization claims like T06A-W3 < T03A-W4). Print violations with
wave numbers (`dep W7 >= W7`) rather than booleans, so a real violation is
actionable in the correction dispatch. Pair with the hash-diff
only-allowlist-changed proof (exactly 2×N diff lines = N changed files ×
old+new) and the cumulative stale-string battery for the complete gate.

Round-trip economics: preflight ~5 min (hash reconcile vs
reviewer-recorded baselines + byte-stability + owner-liveness via
state.db), dispatch→exit ~60 min on alpha/max for a full-DAG rewrite,
independent gate battery ~10 min. Tracker lost the session id at exit
(`not_found`) — tee'd log TASK_SUBMITTED banner + REPORT append were the
ground truth, consistent with pitfall 54.

## Correction round FOUR on the PLAN — ID-split edition (C4 pattern, 2026-08-23)

Fourth CHANGES_REQUESTED (S11-P02D-C4): five findings that SPLIT an existing
ID and ADD a new production Task ID. Same owner-session resume + hash-baseline
+ cumulative-regression discipline as C1–C3, plus lessons specific to
plan-structure surgery:

### Findings that change the ID COUNT are the heaviest round type

C4 renamed `T06A` → `T06A1` AND added `T06A2` (calibration fixtures) and
`T03G` (durable check-run authority): 17→19 IDs, 12→14 waves, and EVERY
downstream artifact of the plan must move in lockstep — headings, wave DAG,
all Depends-on lines of dependents (T03A now needs T06A2; T04A/B/C/T05A/T06B
all add T03G), shared-file ownership matrix rows, trace matrix rows+count
text ("(19 IDs)"), self-check §8 counts, plus every prose mention of the old
ID name. Enumerate this touchpoint list EXPLICITLY in the dispatch prompt;
the worker's own 14-step plan mirrored it and nothing went stale.

### Dispatch mechanics for very large prompts

A 12KB correction prompt passed inline to bash `-q '...'` died on quoting
BEFORE hermes started (`unexpected EOF while looking for matching '''`; log
file never created). Pattern: write_file → `%TEMP%/<lane>_prompt.txt`, then
background-launch with `PROMPT=$(cat <file>) && hermes chat --resume <sid>
... -q "$PROMPT" > <log> 2>&1`. Verify the log exists and grows before
entering monitor waits. Also expect a foreign lane to COMMIT inside your
preflight window on a shared worktree (observed dirty 508→1, HEAD moved);
pin ACTUAL head at preflight, re-pin protected hashes after any foreign
commit, and note output/** git-ignored artifacts stay byte-stable across
commits so the hash-diff allowlist proof survives.

### Manager gate battery additions for C4-type rounds

- Field-presence greps per BINDING BULLET against the worker's block text —
  do NOT accept the worker's "ALL PASS" self-check as coverage. C4's worker
  reported 12/12 while omitting T03G's mandated outcome clause "client KHÔNG
  chọn handler/provider/detector implementation và KHÔNG tạo QCItem trực
  tiếp"; the manager's own grep caught it. One-finding residue ⇒ MICRO-FIX
  resume of the SAME owner naming the exact insertion anchor + verbatim
  clause + "no other changes" — landed first-try in 13 min.
- Parser-flag triage before believing flags: abbreviation deps
  (`T03B/C/D/E` = four IDs), explicit negations (`(+ T06B không ràng buộc)`
  cites an ID to DENY dependence), and stale strings living ONLY inside the
  prompt-mandated history line or a self-check row DESCRIBING the grep (=0)
  are all legitimate. Read each flag's context; record parser artifacts as
  resolved in the verification table.
- Trace-matrix order may follow HEADING/wave order rather than the parent
  prompt's list order — assert set-equality + uniqueness + count, not raw
  sequence equality, unless the reviewer demanded an order.
- Foreign-writer dirty drift during YOUR run (1→13 tracked-modified) is not
  your incident when the paths belong to another lane's allowlist
  (`app/adapters/renderer/*` under S09-T00-I02); attribute by cmdline scan +
  mtime windows, note cross-lane activity in the coordination report.

### Round-trip economics

Round-trip economics: preflight ~5 min (hash reconcile vs Codex baseline + byte-stability ×2 ≥2s +
psutil open_files collision check + owner liveness); dispatch→exit 53 min
(C4 full restructure, alpha/max) + 13 min (R2 micro-fix); independent gate
battery ~10 min. Cumulative stale-string battery from C1/C2/C3 re-grepped
clean — zero regression across four rounds.

## Correction round FIVE on the PLAN — micro-surgical edition (C5 pattern, 2026-08-24)

Fifth CHANGES_REQUESTED (S11-P02D-C5) is the OPPOSITE shape of C4: zero
structural surgery — exactly four stale sentences left over from earlier
rounds (wave refs written before the C4 split renumbered waves: Decision C
"W4 mở chỉ sau T03A" → W6; T03A outcome "registry sẵn sàng cho W4 đăng ký"
→ W6 detector tasks; T03D acceptance "tổng W4 = đủ 8 codes" → tổng W6;
T03F fixture "(T06A)" → "(T06A1)") plus ONE authority-note paragraph
(lane proposals superseded by frozen Decisions A/D/G). Economics: 10m28s
dispatch→exit vs 53 min for C4 — surgical rounds should be CHEAP when you
remove all interpretation room.

### Locate every stale sentence YOURSELF pre-dispatch; pass line-level verbatim replacements

Grep the active body for each finding pattern, print the FULL line, and put
each fix in the dispatch prompt as an exact old→new string pair WITH its
location ("§2 Decision C ô cột cuối: `T03A; W4 mở chỉ sau T03A
MANAGER_VERIFIED` → `T03A; W6 mở chỉ sau T03A MANAGER_VERIFIED`").
Paraphrasing a surgical finding ("fix the stale wave refs in T03A") invites
hunting, guessing, or a spurious BLOCKED. Verbatim pairs landed first-try.

### Legit-occurrence allowlist for token sweeps

When the finding bans stale mentions of a token (wave `W4`, bare ID `T06A`),
the prompt must ALSO enumerate every LEGITIMATE occurrence to preserve:
history line (prior revs may cite old names), DAG diagram row (`W4  T06A2`),
the heading itself (`### W4 · T06A2`). Post-exit gate asserts BOTH
directions: banned patterns = 0 in the active body AND legit occurrences
still present — over-eager sweeps destroy valid content too.

### Full-run-dir inventory diff beats pairwise hash pins

Snapshot sha256 of EVERY file under the run dir into one JSON inventory
before dispatch (20 files here, not just the 2 synthesis files); after exit,
changed-set must equal the allowlist exactly AND new_files must be NONE.
A 2-file pin cannot catch part-file/artifact creation next door; the
inventory loop costs seconds.

### REPORT history-order gate

Append-only REPORTs accumulate one section per round; a worker can insert
the new section at a wrong offset with everything else perfect (this round's
worker did — caught it itself mid-run and relocated the block). Manager gate:
find() positions of every history marker strictly increasing
(C1 < C2 < C3 < C4 < R2 < C5). Assert ORDERING, not just presence.

### Manager-side verifier false-fails: pull anchor strings FROM the live text

Two of the manager's OWN gate greps returned FAIL against correct text:
anchor `CHỈ theo Decisions A/D/G` missed because the note reads "CHỈ ĐƯỢC
theo", and a Decision-A anchor omitted "/PUT/PATCH". An acceptance grep whose
anchor was typed from memory can accuse clean documents. Rule: before ruling
FAIL, print the full section and check semantic presence under different
wording; copy anchors from the LIVE text or make them regex-tolerant; record
dismissed false-fails in the verification table alongside parser artifacts
(pitfall 60 of worker-orchestration SKILL.md). Mirror lesson: the worker
self-disclosed both of ITS check errors in REPORT (wrong self-check anchor;
misplaced insert) — verify disclosures independently, but treat
disclosure-plus-self-correction as the behavior that makes single-round
micro-surgery trustworthy; credit it in the report instead of escalating.
