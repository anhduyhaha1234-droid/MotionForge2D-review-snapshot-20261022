# G1 Q/T Matrix Mapping — Engineering Batch Candidate 01

Trạng thái được xác lập trung thực theo quy tắc Cổng G1 (chưa qua render GPU):
- Các tiêu chí kỹ thuật mã nguồn/gate/provenance (Q05, Q07, T07, T11, T13, T14) đã được kiểm chứng và đạt **PASS** trên 76 bài test thực tế.
- Các tiêu chí chất lượng media thực tế (Q01, Q02, Q03, Q04, Q06, Q08, Q09, Q12) được giữ nguyên trạng **FAIL** hoặc **UNKNOWN** theo đúng baseline Codex 14/10; tuyệt đối không tự gắn PASS khi chưa chạy render GPU ở Gói B.

## 1. Canonical Q Matrix (Q01–Q12)

| Q | Tiêu chí | Trạng thái G1 | Bằng chứng kiểm chứng | Kế hoạch đóng (Gói B/C) |
|---|---|---|---|---|
| **Q01** | CAST identity, pose, reference binding | **FAIL** (giữ nguyên baseline) | Đã có hợp đồng provenance per-actor (A1). Chưa render GPU candidate mới. | Gói B1/B2: Render các excerpts khó (S22/S31/S33/S61) và pilot 300s. |
| **Q02** | Role/count/visibility/global ledger | **FAIL** (giữ nguyên baseline) | Ledger đồng bộ event fids và class windows (A3). Chưa render GPU. | Gói B1/B2: SAM2 mask đúng actor, không ghost/thêm đầu. |
| **Q03** | Contact và event timing | **FAIL** (giữ nguyên baseline) | Đã sửa mapping f/frame và split run không qua hard cut (A3). CoTracker strip đã sửa. | Gói B1: CoTracker reader chạy trên video render thật. |
| **Q04** | Ghost, source-copy, props/background | **FAIL** (giữ nguyên baseline) | Bound check và crop/stitch roundtrip đã verified (A3). | Gói B1: Excerpt S33, S61, S73 book contact. |
| **Q05** | Semantic gate trên actual consumers | **PASS** (Engineering) | Đã đóng: assembler gọi gate trước encoder (A4), batch conformance gate, fail-closed tests. | Duy trì kiểm chứng tại G2 và G3. |
| **Q06** | VACE paired/perturb proof | **UNKNOWN** (giữ nguyên) | Chưa chạy lại inference VACE trên candidate mới. | Gói B1: Paired trial S62/S73 sau khi có quyền GPU. |
| **Q07** | Complete consumed-input cache/provenance | **PASS** (Engineering) | Đã đóng toàn diện: A1 (per-actor v4) + A2 (asset v4) + C02A/C02B1. Invalidation 100% same-path same-size. | Hoàn thành ở Gói A. |
| **Q08** | Frame/cut/fps/duration/A-V technical contract | **PASS** (kỹ thuật cũ) / **UNKNOWN** (cho video mới) | Master cũ PASS 9000f/300s/lag 0ms. Video candidate mới sẽ kiểm lại khi render. | Gói B2: Chạy ffprobe và lag check trên pilot mới. |
| **Q09** | Held-out semantic visual QA | **FAIL** (giữ nguyên baseline) | Chưa có candidate media mới để thẩm định hình ảnh. | Gói B2: Manager QA độc lập trên pilot 300s. |
| **Q10** | Manifest/terminal/checkpoint trung thực | **PASS** (Engineering) | Checkpoint, manifest, diff, test results nhất quán 100%, không bịa log. | Duy trì xuyên suốt các chặng. |
| **Q11** | Concurrency/lease/dispatch harness | **PASS** (Engineering) | Đã kiểm chứng 18 lease RELEASED, 0 writer cạnh tranh, mô phỏng barrier race 2 controller 1 winner. | Duy trì khi dispatch GPU. |
| **Q12** | Upstream adoption thực tế | **FAIL** (giữ nguyên baseline) | Code adapter, stitch, trim, cotracker đã kết nối; chờ output thật từ GPU. | Gói B2: Full pilot 300s chứng minh tích hợp end-to-end. |

## 2. Technical Conformance (T01–T15) Mapping

- **T04 (CropAndStitch)**: PASS trên landmark roundtrip và bound check.
- **T06 (Rerender stage-2)**: PASS cơ chế run decomposition không qua hard cut và fail-closed khi run con lỗi.
- **T07 (Provenance & Cache)**: PASS hoàn toàn qua `r6_key_deps_v4_per_actor` và `r6_key_deps_v4_asset`.
- **T08 (CoTracker contract)**: PASS tensor validation `(T,N,2)` / `(T,N)`, sửa hiển thị side-by-side.
- **T11 (Assembler pre-encoder gate)**: PASS fail-closed trước khi ffmpeg encoder được gọi.
- **T13 (Controller mutex & race barrier)**: PASS trên kiểm tra liveness và mô phỏng 2-controller barrier.
- **T01, T02, T03, T05, T09, T10, T12, T15**: Giữ nguyên trạng thái chờ media render ở Gói B.
