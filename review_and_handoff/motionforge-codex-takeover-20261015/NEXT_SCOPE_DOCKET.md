# Open engineering/media work after C01

This is a dependency docket, not active dispatch or acceptance. C01 has sole write ownership until submitted and independently reviewed. Keep canonical Q01–Q12 meanings; no whole Q05 or parent closure from C01 tests.

## C02 candidate — actual dependency identity and reuse

Read current files again after C01 bytes are frozen. Baseline inspection15Oct:

- r6_cache.verify_deps only hashes source/model if recorded sha256 is truthy; absent source/model fields can return ok. Require reproduction and mandatory schema/identity validation, including true unchanged reuse positive.
- r6_cache.settings_now returns mode/steps/context factor/seed offset/model object, while r6_keygen.build_deps passes model string/steps/sampler/cfg/seed, and r6_keygen_asset passes only mode/steps. Current settings comparison may invalidate every legitimate output. Trace producer and consumer before choosing a shared schema; do not remove comparison to make reuse pass.
- Follow-up source trace16Oct: the per-actor path actually calls skip_allowed;
  its crop default is1.02 while cache settings default1.3, and producer metadata
  omits the effective seed offset. The asset path currently does not call
  skip_allowed at all. root-review/c02-baseline proves the helper rejects the
  asset producer settings unchanged; it is not an end-to-end asset reuse test.
  Include actual producer/consumer wiring proof before claiming reuse works.
- r6_keygen records one graph (target_entities[0]) despite per-actor generation. Establish all consumed graphs/ref/mask/source/model/settings paths from actual pipeline; preserving a deps JSON hash alone does not prove these current files still match.
- r6_gate.key_inputs_now hashes stored deps JSON; it does not rehash underlying model/source/refs. A complete record can still be stale relative to current consumed bytes. C01 only closes missing binding/type/identity cases.

Likely next focused scope after independent approval: r6_cache.py, r6_keygen.py, r6_keygen_asset.py, necessary r6_gate.py wiring, new CPU dependency tests and per-task evidence. Only authorize after a root packet with concrete current repro/AC, preimages and exact owner. Existing media/reviews remain immutable; historical cache may correctly become invalid.

## Later dependencies

Event-key propagation and child-result/manifests; CoTracker semantic paired queries and evidence; independent VACE trim/perturb proof; controller/lease races; fresh actual media correction and held-out semantic review; exact300s pilot export/AV; then app/tool integration and full22-minute source. Reuse pinned upstream stack and keep GPU1. None is accepted from file counts, exit0, a hash, or a PASS string.

R6g did not deliver new master/comparison. R6f source/master/comparison hashes remain in PREFLIGHT.json. Dense visual semantic acceptance and canonical correction matrix remain open.
