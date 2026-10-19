---
name: bom-contradiction-hunter
description: Actively search for contradicting evidence in research.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, adversarial, verification]
---

# bom-contradiction-hunter

## When to Use

**Positive triggers:**
- A research conclusion feels too clean or one-sided.
- A high-stakes claim is supported by only favorable evidence.
- Before finalizing a niche opportunity assessment.

**Negative triggers:**
- The topic has well-established consensus.
- The user explicitly says to skip adversarial checks.
- The claim is trivial.

## Required Inputs

- Claims or conclusions to challenge.
- The existing evidence supporting those claims.
- How high the stakes are.

## Procedure

1. For each key claim, formulate the strongest possible counter-claim.
2. Search specifically for evidence supporting the counter-claim.
3. Look for: failure cases, market exits, negative reviews, regulatory warnings, expert criticism.
4. Check if supporting evidence comes from biased sources (vendors, investors, affiliates).
5. Assess whether the claim survives the adversarial search.
6. If the claim weakens, update the confidence tier and note the contradicting evidence.

## Decision Rules

- Never skip adversarial search on opportunity conclusions.
- A claim from a single biased source (vendor, affiliate) requires independent verification.
- Contradicting evidence gets equal presentation weight.
- If adversarial search finds strong counter-evidence, the conclusion must be revised.

## Pitfalls

- Confirmation bias: only searching for evidence that supports the conclusion.
- Dismissing negative evidence as outliers.
- Not checking the bias of supporting sources.
- Treating lack of contradicting evidence as proof the claim is correct.

## Verification

- Each key claim has had at least one adversarial search.
- Source bias is noted for all supporting evidence.
- Contradictions are documented, not suppressed.
- Confidence tiers reflect adversarial findings.

## Output Format

- Claims challenged and results.
- Counter-evidence found with sources.
- Revised confidence tiers.
- Weakest claims flagged for further investigation.
