---
name: hermes-skill-authoring
description: "Create, validate, install, and evaluate batches of Hermes skills."
tags: [hermes, skills, authoring, validation, bundling, evals]
---

# Hermes Skill Authoring

## When to Use

- Creating one or more new Hermes skills from scratch.
- Building a BOM (Bill of Materials) — a portable skill bundle with profiles, bundles, evals, and install scripts.
- Validating skill structure before installation.
- Writing trigger evals or execution evals for skill groups.
- Reviewing or patching existing skills for structural compliance.

## Required Inputs

- Skill name(s) and purpose.
- Source methodology or domain knowledge to synthesize.
- Target Hermes profile (which skills to install).
- Whether to create evals (trigger, execution, or both).

## Procedure

### 1. Skill Structure Requirements

Every SKILL.md MUST pass the BOM validator (`scripts/validate_skills.py`):

- **YAML frontmatter** with `name` matching the directory name exactly.
- **`description`** ≤ 60 characters.
- **Seven required sections** (exact headings):
  - `## When to Use`
  - `## Required Inputs`
  - `## Procedure`
  - `## Decision Rules`
  - `## Pitfalls`
  - `## Verification`
  - `## Output Format`
- **≤ 5000 words** total.

### 2. When to Use — Trigger Design

Each skill needs **positive triggers** (when it should fire) and **negative triggers** (when it should NOT):

- Positive triggers describe the **situation**, not keywords. Match on intent, not word overlap.
- Negative triggers catch subtle misfires: "Explain CPU cache" should NOT trigger `bom-cache-friendly-prompting`.
- Include edge cases: near-miss negatives that a keyword matcher would false-positive on.

**Trigger eval pattern:** Keyword-based matching is too crude. Use semantic evaluation:
- Read the skill's When to Use section.
- For each positive test prompt, verify the *situation* matches the trigger description.
- For each negative test prompt, verify the situation does NOT match.
- A prompt like "Explain CPU cache" shares keywords with cache-optimization skills but is a definitional question, not an optimization request.

### 3. Evidence-Tier Skills (Research Domain)

When creating research-domain skills, embed epistemic rules. Full reference: `references/research-epistemic-rules.md`. Summary:

- **Distinguish:** signal (early indicator) / evidence (directly supports) / inference (derived) / assumption (no evidence).
- **Date-stamp** all data: retrieval date mandatory, publication date best-effort.
- **Seek contradicting evidence** actively — never skip adversarial search on opportunity conclusions.
- **No market size claims** without primary data.
- **No search volume as sole evidence** — combine with competition, intent, content quality.
- **No SEO aggregation articles** as primary sources.
- **Every opportunity requires a validation experiment** — next step to confirm or disprove.
- **Low competition ≠ opportunity** — investigate WHY competition is low before concluding.

### 4. Bundle Format

Bundles are YAML files in `~/.hermes/skill-bundles/`:

```yaml
name: <bundle-name>
description: <one-line description>
skills:
  - skill-name-1
  - skill-name-2
instruction: |
  Pipeline instruction describing execution order and constraints.
```

The `instruction` field defines the pipeline order and any cross-cutting constraints.

### 5. Installation

- Install skills as **symlinks** from the BOM source to `~/.hermes/skills/<skill-name>/`.
- **Never `rm -rf`** existing skills — check for existence first, skip or report conflicts.
- Install bundles by copying YAML to `~/.hermes/skill-bundles/`.
- Check for **name collisions** with existing skills before installing (different namespaces = OK, same name = conflict).

### 6. Eval Design

**Trigger evals** (`evals/<group>-trigger-evals.json`):
```json
{
  "skill-name": {
    "positive": ["prompt that should trigger", ...],
    "negative": ["prompt that should NOT trigger", ...]
  }
}
```

**Execution evals** (`evals/<group>-execution-evals.json`):
```json
{
  "evals": [
    {
      "id": "eval-01",
      "skill": "skill-name",
      "input": "test input",
      "expected_output": { ... },
      "pass_criteria": "human-readable criteria"
    }
  ]
}
```

Execution evals test whether the skill produces correct structured output, not just whether it triggers.

### 7. Incoming Skill Pack Analysis (analyze BEFORE install)

When the user hands over a skill pack/ZIP (or any external artifact) and asks to "analyze" / "prepare" / "review" it:

1. Extract to a temp dir and read README.md first, then every SKILL.md and its `references/` files. Note name conflicts (`ls skills/<category>/`) and overlap with existing umbrellas.
2. Run **read-only readiness probes** (never configure/test): local service health (`curl -m 4 http://localhost:PORT/` — a 404 on /health with a live root means the server is up), provider credential presence (minimal authenticated call), Python deps (`python -c "import <pkg>"`), env keys.
3. Deliver: feature table per skill, strengths/weaknesses (including compatibility with current config, e.g. max_spawn_depth), credential requirements table (required vs optional + where to get), machine status.
4. STOP there. List the install plan but do NOT execute it until the user provides credentials and says go. The user's stated workflow: analyze first, report what credentials are needed, they supply them — "chưa cần dùng ngay" (no need to use it right away).

Full checklist: `references/incoming-skill-pack-analysis.md`.

## Decision Rules

- Description ≤ 60 chars — validate before writing, not after.
- All 7 sections required even if brief.
- One skill = one concern. Don't combine unrelated responsibilities.
- Skills are class-level: name describes a *type of work*, not a specific task.
- Negative triggers are as important as positive triggers — invest effort in edge cases.

## Pitfalls

1. **Description too long.** The validator rejects >60 chars. Write description first, validate length, then write body.
2. **Missing sections.** The validator checks for all 7 exact headings. Even a one-liner section is fine.
3. **Keyword-based trigger evals are unreliable.** Simple word overlap produces both false positives and false negatives. Use semantic evaluation — read the skill's When to Use, then judge whether the test prompt's *situation* matches, not whether words overlap.
4. **`execute_code` timeout on batch file writes.** Writing 5+ files in a single `execute_code` script can timeout. Use individual `write_file` calls for reliability, or split into smaller batches (≤4 files per call).
5. **Symlinks on Windows.** Creating symlinks in git-bash requires running as admin or enabling developer mode. If `ln -s` fails, fall back to copying.
6. **Overwriting existing skills.** Always check `ls ~/.hermes/skills/<name>` before installing. Report conflicts to user.
7. **Frontmatter `name` must match directory name exactly.** A skill in `bom-my-skill/SKILL.md` must have `name: bom-my-skill`.
8. **MSYS `/tmp/` path breaks Python `open()`.** On Windows, shell commands in `terminal()` auto-resolve MSYS paths (e.g., `/tmp/hermes-skills-bom/`), but Python's `open()` does not — it sees the literal `/tmp/` and raises `FileNotFoundError`. When writing trigger-eval scripts in Python, always use the Windows-native path: `C:/Users/Admin/AppData/Local/Temp/` instead of `/tmp/`.
9. **Bilingual trigger evals.** When skills serve a non-English user, write trigger evals in both the user's language and English. A Vietnamese research skill should have Vietnamese positive triggers alongside English ones. This tests that triggers fire on intent, not language.
10. **Pipeline bundle `instruction` field.** The bundle YAML's `instruction` field should describe the execution pipeline order with explicit arrows (→) and cross-cutting constraints (epistemic rules, date-stamping, evidence requirements). This becomes the agent's runtime directive when the bundle loads.
11. **Agent-created vs bundled skills.** Skills created by the agent (not shipped with Hermes) can be patched via `skill_manage(action='patch')`. Bundled skills (created_by=None in the skill records) are off-limits to autonomous curation — only the user or the curator can modify them. Do not attempt to patch bundled skills; instead create a new agent-created skill or extend an existing agent-created umbrella.
12. **Injection-triggering language in third-party skills.** External packs often ship "MUST USE" / "ALWAYS" / "NEVER" / "DO NOT" / "CRITICAL" language that trips Hermes' prompt-injection detector on load; the agent then burns iterations trying to patch the skill instead of doing the work. Soften to "Recommended for" / "avoid" during install (the deep-research pack's own pitfalls document this exact failure).
13. **Analyze-first scope discipline.** When the user asks to analyze/prepare an incoming artifact, installing, configuring, testing, or deep credential-hunting (probing APIs, dumping config DBs) before approval is out of scope. The deliverable is the analysis + credential requirements; the user explicitly supplies credentials afterward — "chưa cần dùng ngay" (no need to use it right away).
14. **Appending to a numbered list with `patch` can collide with numbers another writer just added.** Two independent insertions of "25./26." into a pitfalls list left duplicate numbers, which makes every later citation of "pitfall N" ambiguous — a silent corruption of a document other agents reference by number. After ANY append to a numbered section, re-scan: `grep -oE '^[0-9]+\.' SKILL.md | sort -n | uniq -d` and renumber before finishing.
15. **A SKILL.md that has grown past the platform limit blocks all growth, including a one-line pointer.** A patch adding a `references/` pointer line was refused with "content is 100,240 characters (limit: 100,000)". The reference file itself still writes fine and is discoverable through `linked_files`, so: put the substance in `references/`, and when the umbrella is over the limit either make the edit net-neutral/negative or note the oversize umbrella for consolidation rather than deleting content to fit a pointer.
16. **Read-before-write is enforced on supporting files too.** `skill_manage(action='patch', file_path='references/x.md')` is refused unless that file's content was loaded in the same turn — even if you just created it with `write_file`. Call `skill_view(name, file_path=...)` first, then patch.
17. **Pair every write with its OWN single preceding load — batched loads+writes get refused.** Measured in a curator review turn: a message with two `skill_view(file_path=...)` loads followed by a message with several writes to those same files had EVERY write refused with `_read_before_write_required`; the identical edits succeeded as strict 1:1 pairs (one load message → one write message → reload → next write). Consequences: (a) don't batch multiple loads hoping to unlock multiple writes; (b) a successful write invalidates that file's load — reload before a second edit to the same file; (c) `remove_file` also requires its own fresh load of the target file, even for a file you created earlier in the same turn.

## Verification

- Run `python scripts/validate_skills.py` — all skills must PASS.
- Run trigger evals — all positive must match, all negative must not.
- Verify symlinks are valid: `ls ~/.hermes/skills/<name>/SKILL.md`.
- Verify bundle exists: `ls ~/.hermes/skill-bundles/<bundle>.yaml`.
- Check no existing skills were overwritten.

## Output Format

- Validation report: PASS/FAIL per skill.
- Installation report: installed/skipped/conflict per skill.
- Trigger eval results: PASS/FAIL per skill.
- Execution eval results: PASS/FAIL per eval case.
- Summary: total counts, conflicts, remaining issues.
