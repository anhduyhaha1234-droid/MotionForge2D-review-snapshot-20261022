# MotionForge2D G1 candidate: g1-candidate-16

Trạng thái: CODE_DONE / PENDING_FROZEN_REPLAY. Chưa có verdict G1; Media/GPU/render vẫn bị chặn.

Base: g1-candidate-11, manifest SHA-256: dcfd666e3c061402cb899b05f1ada23f1a40274b7cfb1e348e45b264118c351f.
Đã sửa 6 file nguồn trong bản sao Codex; chi tiết và preimage/postimage ở SOURCE_CHANGES.json, DIFF.patch.

Q05 hiện chạy lại test thật bằng pytest/JUnit, so node IDs/exit với receipt và hash test; Q07 yêu cầu dependency record v4 cho từng shot, so hash và chạy lại validator. Adapter không phát TASK_SUBMITTED khi gate từ chối.

Bản này cần chạy guard độc lập trên candidate copy trước khi nêu số test PASS. Không dùng kết quả test của owner worktree thay cho guard.
