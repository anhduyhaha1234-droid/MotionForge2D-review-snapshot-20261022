# G1 Q/T Matrix Mapping — Candidate 04 (Correction G1-R1)

Được xác lập trung thực theo quy tắc Cổng G1 (§0.12):
- Toàn bộ các tiêu chí kỹ thuật mã nguồn, provenance, gate, và race barrier (**Q05, Q07, Q10, T04, T06, T07, T08, T11, T13, T14**) đã đạt **PASS** trên 89 bài test và 20/20 hàng matrix M01–M20 (8 verified bởi root + 12 closed trong candidate 04).
- Các tiêu chí chất lượng media thực tế (**Q01, Q02, Q03, Q04, Q06, Q08, Q09, Q12**) được giữ nguyên trạng **FAIL** hoặc **UNKNOWN** theo đúng baseline Codex 14/10; các kết xuất B1 sơ bộ được đánh dấu **UNREVIEWED** và sẽ được nghiệm thu tại Cổng G2 (Pilot 300s).

## 1. Canonical Q Matrix (Q01–Q12)

| Q | Tiêu chí | Trạng thái G1-Candidate-04 | Bằng chứng kiểm chứng | Kế hoạch đóng (Gói B/C) |
|---|---|---|---|---|
| **Q01** | CAST identity, pose, reference binding | **FAIL** (giữ nguyên baseline) | Đã có hợp đồng provenance per-actor (A1) & asset (A2). Media chưa duyệt. | Gói B1/B2: Render các excerpts và pilot 300s. |
| **Q02** | Role/count/visibility/global ledger | **FAIL** (giữ nguyên baseline) | Ledger đồng bộ event fids và class windows (A3/R05). | Gói B1/B2: SAM2 mask đúng actor, không ghost. |
| **Q03** | Contact và event timing | **FAIL** (giữ nguyên baseline) | Đã sửa mapping f/frame, chuyển trạng thái và split run không qua cut (A3/R05). | Gói B1: CoTracker reader chạy trên video render thật. |
| **Q04** | Ghost, source-copy, props/background | **FAIL** (giữ nguyên baseline) | Bound check và crop/stitch roundtrip đã verified (A3). | Gói B1: Excerpt S33, S61, S73 book contact. |
| **Q05** | Semantic gate trên actual consumers | **PASS** (Engineering) | Đã đóng: assembler gọi gate trước encoder (A4), batch conformance gate mode strict (R06), AST parse test file, fail-closed tests. | Duy trì kiểm chứng tại G2 và G3. |
| **Q06** | VACE paired/perturb proof | **UNKNOWN** (giữ nguyên) | Chưa chạy lại inference VACE trên candidate mới. | Gói B1: Paired trial S62/S73 sau khi có quyền GPU. |
| **Q07** | Complete consumed-input cache/provenance | **PASS** (Engineering) | Đã đóng toàn diện: A1 (per-actor v4) + A2 (asset v4 bắt buộc grey_ref & euler sampler R01) + same-path same-size invalidation. | Hoàn thành ở Gói A. |
| **Q08** | Frame/cut/fps/duration/A-V technical contract | **UNKNOWN** (cho video mới) | Master cũ PASS 9000f/300s/lag 0ms. Video candidate mới sẽ kiểm lại khi render. Video giả (ftyp+xxxx) bị ffprobe chặn triệt để. | Gói B2: Chạy ffprobe và lag check trên pilot mới. |
| **Q09** | Held-out semantic visual QA | **FAIL** (giữ nguyên baseline) | Chưa có candidate media mới để thẩm định hình ảnh. | Gói B2: Manager QA độc lập trên pilot 300s. |
| **Q10** | Manifest/terminal/checkpoint trung thực | **PASS** (Engineering) | Manifest lọc relative path chuẩn xác (R07), checkpoint, manifest, diff, test results nhất quán 100%. | Duy trì xuyên suốt các chặng. |
| **Q11** | Concurrency/lease/dispatch harness | **PASS** (Engineering) | Đã kiểm chứng 18 lease RELEASED, 3 script hashes khớp historical 34/34 (R08), sandbox 2-process barrier race 1 winner (M18). | Duy trì khi dispatch GPU. |
| **Q12** | Upstream adoption thực tế | **FAIL** (giữ nguyên baseline) | Code adapter, stitch, trim, cotracker đã kết nối; chờ output thật từ GPU. | Gói B2: Full pilot 300s chứng minh tích hợp end-to-end. |

## 2. Technical Conformance (T01–T15) Mapping

- **T04 (CropAndStitch)**: PASS trên landmark roundtrip và bound check.
- **T06 (Rerender stage-2)**: PASS cơ chế run decomposition không qua hard cut, frame naming toàn cục (0011..0020), và fail-closed khi run con lỗi (R04).
- **T07 (Provenance & Cache)**: PASS hoàn toàn qua `r6_key_deps_v4_per_actor` và `r6_key_deps_v4_asset` (R01).
- **T08 (CoTracker contract)**: PASS tensor validation `(T,N,2)` / `(T,N)`, vis binary/[0,1], sửa CLI --help (R02), frame 43 preserved, no-NaN JSON (R03).
- **T11 (Assembler pre-encoder gate)**: PASS fail-closed trước khi ffmpeg encoder được gọi.
- **T13 (Controller mutex & race barrier)**: PASS trên kiểm tra liveness và mô phỏng 2-process barrier.
- **T01, T02, T03, T05, T09, T10, T12, T15**: Giữ nguyên trạng thái chờ media render ở Gói B.
