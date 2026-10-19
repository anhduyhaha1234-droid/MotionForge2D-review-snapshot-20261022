**Session Opening Proposal — G1-R1; PREPARED, NOT DISPATCHED.**

- Decision: resume same task/lineage `MF-DEMO-LONG-01`, correction G1-R1 after `g1-candidate-01 CHANGES_REQUESTED`. Không restart A1 từ checkpoint015 hoặc khôi phục source cũ đè live.
- Current real Hermes session: `20261017_115944_b2a338`; `gemini-implementation-owner` là label. Old Sol/DeepSeek sessions không phải target. Fresh owner/context/liveness preflight phải xác minh trước ghi; snapshot reviewer chỉ để điều tra.
- Model: `ag/gemini-3.8-flash-high` qua `http://127.0.0.1:20128/v1`; no fallback. Reasoning giữ effective provider-supported config, không bịa gán GPT Max cho Gemini. Không đổi globals/router/account để né quota.
- Context health: stale checkpoint/overclaims đã được ghi R09. Đọc rules đầy đủ; nạp review + matrix + current packet và đúng 2–4 skills liên quan mỗi task. Checkpoint sau coherent unit. Nếu context audit không đạt, chỉ chuyển owner sau old writer/children terminal và receipt transfer thật, không tự tạo lineage thứ hai.
- Dependency: R01–R09 chưa đóng; candidate01 hash không đồng nhất live gate. Freeze/reconcile trước sửa. Không cần đợi user chọn implementation routine trong write-set đã mở.
- Maximum safe wave: 1 production writer; có thể 1–2 subagents chỉ đọc/QA trong sandbox riêng nếu runtime hỗ trợ, không cùng sửa tree. Manager giữ registry/evidence; không hai writer. GPU=0 cho correction engineering này.
- Exclusive production write-set: R6/scripts/r6_cache.py, r6_cotracker.py, r6_propagate.py, r6_ledger.py, r6_gate.py, r6_matrix.py; r6_key_recipe.py, r6_keygen_asset.py, r6_assemble.py chỉ khi actual repro/call path cần, preimage riêng trước patch. Test mới `R6/tests/test_g1_r1_*.py`; existing tests patch-only nếu bổ sung assertions, tuyệt đối không giảm/xóa checks. Một submission builder mới chỉ trong `execution/G1-R1/`.
- Evidence write-set: `execution/G1-R1/**`, checkpoint/state hiện hành sau snapshot và reconciliation; candidate02 mới. Candidate01/root review packet, old media/receipts/terminals/proofs read-only.
- Protected: MAIN/INTEGRATION source/DB, prior reviews, R4/R5, source/CAST, weights/runtime, controller harness/upstream vendor, production media, old test semantics. Không Git mutation, full-file replace, blanket cleanup hoặc inference/render.
- Self-review: implement → isolated real-consumer probes → 20-row matrix → regression → independent QA subagent nếu có → fix trong cùng scope → freeze candidate02 → report. QA tự duyệt không cấp Codex approval.
- Dispatch authority: user nhận prompt để gửi owner; Codex không dispatch hay restart schedule từ review này. Prompt này chỉ sửa G1 theo yêu cầu hiện tại §0.12; thay orchestration sang end-to-end là thay đổi tách biệt, không dùng để nâng verdict candidate01.

Prompt khớp proposal: [PROMPT_SUA_G1_VI.md](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/PROMPT_SUA_G1_VI.md). Review và matrix là đầu vào bắt buộc.
