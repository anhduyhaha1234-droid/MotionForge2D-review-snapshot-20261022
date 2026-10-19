# Research-Domain Epistemic Rules

Standard epistemic constraints to embed in research-domain SKILL.md files.
Use when creating skills for market research, niche analysis, competitive intelligence,
or any domain where evidence quality matters.

## Evidence Tier Classification

Every evidence item must be classified:

| Tier | Definition | Example |
|------|-----------|---------|
| **Signal** | Early indicator, not yet evidence | GitHub repo with low stars but active commits |
| **Evidence** | Directly supports a claim | Official pricing page, published study |
| **Inference** | Derived from evidence + reasoning | "Market growing because 3 new entrants this quarter" |
| **Assumption** | No supporting evidence | "Users probably want feature X" |

## Mandatory Rules for Research Skills

Embed these in every research SKILL.md's Decision Rules or Verification section:

1. **Date-stamp all data.** Retrieval date mandatory. Publication date best-effort.
   Format: "Data retrieved YYYY-MM-DD."

2. **Distinguish signal/evidence/inference/assumption** in every output.
   Never present inference as fact. Never present signal as evidence.

3. **Actively seek contradicting evidence.** Before finalizing any conclusion,
   search for counter-evidence. A conclusion that survives adversarial search
   is stronger than one that was never challenged.

4. **No market size claims without primary data.** Citing a vendor blog's
   "market will reach $65B by 2027" without triangulating from 2+ independent
   sources is not evidence.

5. **Search volume ≠ sole evidence.** High search volume indicates interest,
   not opportunity. Combine with: competition intensity, content quality,
   monetization clarity, user intent classification.

6. **No SEO aggregation articles as primary sources.** Blog posts that compile
   "Top 10 tools for X" are secondary summaries, not evidence. Always trace
   back to the primary source.

7. **Every opportunity requires a validation experiment.** Never conclude
   "this is an opportunity" without proposing: "To validate, do X and expect Y.
   If Z instead, the opportunity is invalid."

8. **Low competition ≠ opportunity.** A market with few competitors may have
   no demand, failed previous attempts, regulatory barriers, or insufficient
   margins. Always investigate WHY competition is low.

## Embedding Pattern

For each research skill, add to Decision Rules:

```
## Decision Rules

- [skill-specific rules...]
- Distinguish signal, evidence, inference, and assumption in all output.
- Date-stamp all data: retrieval date mandatory.
- Actively seek contradicting evidence before concluding.
```

And to Verification:

```
## Verification

- [skill-specific checks...]
- No claim is presented as evidence without meeting the evidence tier criteria.
- Contradicting evidence is documented, not suppressed.
- Data freshness is stated.
```
