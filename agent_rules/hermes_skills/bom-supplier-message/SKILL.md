---
name: bom-supplier-message
description: Write concise, natural supplier messages.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: work
    tags: [supplier, message, email]
---

# bom-supplier-message

## When to Use

- Writing or rewriting an English supplier email, KakaoTalk message, or short business follow-up.
- The user needs polite but non-stiff wording.

## Required Inputs

- Recipient name if known.
- Business context and exact request.
- Required dates, amounts, codes, attachments, and preferred channel.

## Procedure

1. Identify the message purpose, required action, and supporting context.
2. Place the action request early and keep one paragraph per topic.
3. Preserve all dates, amounts, codes, addresses, and logistics details exactly.
4. Use natural business English with gentle wording and no unnecessary ceremony.
5. Remove repetitive thanks, apologies, and pressure phrases.
6. Check whether the output should be an email or a short chat message.

## Decision Rules

- Avoid “at your earliest convenience,” “willing to consider,” and repeated “thank you for your flexibility.”
- Do not add deadlines or commitments not supplied by the user.
- Use a professional, friendly tone rather than legalistic language.
- For email, include a clear subject only when requested or appropriate.

## Pitfalls

- Translating Vietnamese word-for-word.
- Repeating the request in the closing.
- Overexplaining internal company procedures.
- Changing the intended level of urgency.

## Verification

- The requested action is unambiguous.
- All business facts match the input.
- Tone is polite, natural, and concise.
- The format fits email or chat as requested.

## Output Format

- Finished send-ready message only, unless explanation is requested.
