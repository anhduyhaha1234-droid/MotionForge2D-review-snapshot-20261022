# R6 checkpoint — Q01–Q12 giữ nguyên định nghĩa

9 FAIL +2 UNKNOWN +1 PASS engineering. Verdict trên checkpoint e3107a52…e48e, không phải final submission. UNKNOWN không được waive.

| Q | Ý nghĩa canonical | Review 14/10 | Evidence / điều kiện đóng |
|---|---|---|---|
| Q01 | CAST identity, refs, pose | FAIL | F01: S22/31/33/61 ghost/pose; source/ref/key/final cùng frame + perturb từng actor, missing ref reject. |
| Q02 | Role/count/visibility/ledger | FAIL | F01: S33/S61 thêm đầu, S62 entry còn mặt nguồn; S63/64 occlusion; S74 cải thiện chưa waive toàn bộ. |
| Q03 | Contact và event timing | FAIL | F01/F03/F04: S73 mất sổ, keys off-grid, CoTracker windows rỗng. |
| Q04 | Ghost, source-copy, props/background | FAIL | F01: portrait S33/S61 và xe ảnh thật S57; giữ control S74, không regression. |
| Q05 | Semantic gate trên actual consumers | FAIL | F02/F07: assembler không gọi gate, empty bindings accepted, final-review/held-out coverage thiếu. |
| Q06 | VACE paired trial/perturb/conformance | UNKNOWN | Có trim và 3 trial receipts; chưa đóng độc lập causal pixels, full bindings/resources/paired controls. Không chạy lại inference chỉ vì review chưa kiểm. |
| Q07 | Dependency/cache đúng consumed bytes | FAIL | F05/F06: source/model mutation vẫn verify; output cũ refresh một frame được nhận mới. |
| Q08 | Frames/cuts/AV/timeline engineering | PASS — engineering | 9000f metadata/300s/30fps/640×360, decode0, audio head/mid/tail lag0ms. Không full playback/listening hay semantic approval. Khi sửa phải rerun AV/cut/seam checks trên exact candidate mới. |
| Q09 | Manager held-out visual QA | FAIL | F07: worker QA dở/sai scope; chưa có Manager QA độc lập trên candidate frozen. |
| Q10 | Manifest/terminal/checkpoint trung thực | FAIL | F07/F08: 40/42 terminal hashes, missing final manifest/matrix, stale remaining_work, remapped Q. |
| Q11 | Concurrency/lease/dispatch harness | UNKNOWN | Manager lưu 51/51 và race34/34; reviewer chưa rerun/đóng toàn bộ suite lượt này. Fail-closed R6f quan sát được; giữ proof đúng hash, không phải bằng chứng harness hỏng. |
| Q12 | Upstream adoption thực tế | FAIL | Upstream stitch/latent trim có tiến bộ; F03/F04/F05 thiếu event/contact/end-to-end proof. Không claim source-ready là pilot-pass. |

Owner mọi sửa media/adapter trong task: worker `20261007_234033_cc0b6d`; Manager `20261012_002032_daa36c` sở hữu coordination/harness/independent QA. Context/incident audit trước continuation; recovery chỉ theo §4 và zero-writer. Không tạo thêm task/session chỉ vì nhiều findings.
