---
name: bom-retry-rate-limit-controller
description: Handle rate limits without wasting repeated calls.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [retry, rate-limit, fallback]
---

# bom-retry-rate-limit-controller

## When to Use

- A provider or tool returns 429, timeout, connection, or transient 5xx errors.
- Calls are being repeated without progress.
- Fallback providers or models are available.

## Required Inputs

- Exact error and status code.
- Attempt count and previous delay.
- Provider retry headers, fallback options, and idempotency risk.

## Procedure

1. Classify the failure as retryable, non-retryable, quota-exhausted, authentication, malformed request, or tool logic.
2. Honor Retry-After or provider guidance when available.
3. Retry only retryable failures, with bounded attempts and jittered exponential backoff.
4. For deterministic requests, reuse the same payload and idempotency key when supported.
5. Fail over after the configured retry threshold rather than exhausting the primary repeatedly.
6. Reduce concurrency or batch size when aggregate rate limits are the cause.
7. Stop and report when quota is exhausted or the request itself must change.

## Decision Rules

- Do not retry authentication, permission, validation, or malformed-request errors unchanged.
- Do not exceed the task retry budget.
- Do not duplicate non-idempotent writes without an idempotency guarantee.
- Record attempts so the same failed path is not restarted by another subagent.

## Pitfalls

- Treating every API error as transient.
- Immediate tight-loop retries.
- Retrying a huge request that should be reduced.
- Failing over without preserving task state.

## Verification

- Retry decisions match error class.
- Attempts are bounded and recorded.
- No duplicate side effect occurred.
- Fallback or stop outcome is explicit.

## Output Format

- Error class.
- Attempts and delays.
- Fallback action.
- Final status.
