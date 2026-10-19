# S03-T03 Start Prompt

Read `TASK.md` and every required source it names before editing. Implement the
complete durable Video Item lifecycle/order contract under the isolated v2
namespace. Preserve all legacy routes and `channels.json`; do not commit.

Treat concurrency as a first-class acceptance criterion: deterministic tests
must cover append/reorder CAS, archive identity-map behavior, and Channel
archive versus new assignment. Run focused and combined suites plus the full
mandatory 7/7 quality baseline, then update `LOG.md` and `REPORT.md` and leave
the task `SUBMITTED` for PM review.

