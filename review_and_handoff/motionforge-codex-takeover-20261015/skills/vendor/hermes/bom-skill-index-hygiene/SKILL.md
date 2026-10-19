---
name: bom-skill-index-hygiene
description: Keep the skill catalog small and precise.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [skills, catalog, trigger]
---

# bom-skill-index-hygiene

## When to Use

- Hermes has many installed skills, overlapping descriptions, or frequent wrong activations.
- Startup context or skill index size is consuming excessive tokens.
- A skill library is being imported or curated.

## Required Inputs

- Installed skill names, descriptions, categories, and usage history.
- Target workflows and available Hermes profiles.

## Procedure

1. Inventory skills and group by actual capability rather than repository source.
2. Identify duplicates, overly broad descriptions, obsolete skills, and skills never used.
3. Keep one default skill per capability; archive alternatives unless they serve a distinct trigger.
4. Rewrite descriptions to state both function and activation scope in minimal language.
5. Move detailed content from SKILL.md to references when it is not required on every activation.
6. Create separate Hermes profiles or selective install profiles for unrelated domains.
7. Run positive and negative trigger tests before keeping the revised catalog.

## Decision Rules

- Do not install a catalog repository wholesale into an active profile.
- Descriptions must not claim broad “help with anything” behavior.
- Archive before delete when usage evidence is uncertain.
- Do not merge skills whose procedures or risk controls conflict.

## Pitfalls

- Believing progressive disclosure makes catalog size free.
- Keeping several near-identical coding or research skills.
- Putting long examples in descriptions.
- Using tags as a substitute for precise descriptions.

## Verification

- Each active skill has a distinct trigger.
- Positive and negative trigger tests pass.
- Unused or duplicate skills are archived or moved to another profile.
- The active catalog token estimate decreases.

## Output Format

- Keep, merge, archive, and remove decisions.
- Description patches.
- Profile recommendation.
- Estimated catalog reduction.
